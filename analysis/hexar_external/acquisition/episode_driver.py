"""Actual development navigation/intervention driver. No explanatory model calls."""
import argparse
import json
import math
import random
import time
from pathlib import Path


def main():
    import rclpy
    from rclpy.node import Node
    from rclpy.action import ActionClient
    from nav2_msgs.action import NavigateToPose
    from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped, Twist
    from std_msgs.msg import Bool, String
    from gazebo_msgs.srv import SpawnEntity, SetEntityState, GetEntityState
    from rclpy.parameter import Parameter
    from rcl_interfaces.srv import SetParameters
    from std_srvs.srv import Empty
    from sampling import sample
    from gazebo_msgs.msg import EntityState
    from action_msgs.msg import GoalStatus
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=("success", "obstacle", "dynamic_env", "localization", "charging", "manual_joystick"), required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--timeout", type=float, default=75)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    rclpy.init()
    node = Node("skill_navigate_to_zone", parameter_overrides=[])
    node.set_parameters([rclpy.parameter.Parameter("use_sim_time", value=True)])
    action = ActionClient(node, NavigateToPose, "/navigate_to_pose")
    if not action.wait_for_server(timeout_sec=90):
        raise RuntimeError("technical invalidity: navigation action server unavailable")
    charging = node.create_publisher(Bool, "/power/is_charging", 10)
    joystick = node.create_publisher(Bool, "/joy_priority", 10)
    joy_vel = node.create_publisher(Twist, "/joy_vel", 10)
    pose_pub = node.create_publisher(PoseWithCovarianceStamped, "/initialpose", 10)
    task_pub = node.create_publisher(String, "/task_info", 10)
    from rclpy.qos import QoSProfile, DurabilityPolicy
    goal_pub = node.create_publisher(PoseStamped, "/hexar_acquisition/navigation_goal", QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))
    sampling = sample(args.seed)
    start_x, start_y = sampling['start_xy']
    target_x, target_y = sampling['goal_xy']
    reposition = node.create_client(SetEntityState, '/set_entity_state')
    ground_truth = node.create_client(GetEntityState, '/get_entity_state')
    if not reposition.wait_for_service(timeout_sec=10) or not ground_truth.wait_for_service(timeout_sec=10):
        raise RuntimeError('technical invalidity: reset verification services unavailable')
    reset = SetEntityState.Request()
    reset.state.name = 'tiago'
    reset.state.pose.position.x, reset.state.pose.position.y = start_x, start_y
    reset.state.pose.position.z = .001
    reset.state.pose.orientation.z = math.sin(sampling['start_yaw']/2)
    reset.state.pose.orientation.w = math.cos(sampling['start_yaw']/2)
    future = reposition.call_async(reset)
    rclpy.spin_until_future_complete(node, future, timeout_sec=10)
    if not future.done() or not future.result().success:
        raise RuntimeError('technical invalidity: robot reposition failed')
    verify = GetEntityState.Request()
    verify.name = 'tiago'
    # Verify measured physics settling over a bounded window. GetEntityState reads
    # the current WorldPose; a single immediate post-reposition read is insufficient.
    reset_measurements = []
    reset_deadline = time.monotonic()+3
    consecutive_in_tolerance = 0
    reset_error = float('inf')
    while time.monotonic() < reset_deadline:
        future = ground_truth.call_async(verify)
        rclpy.spin_until_future_complete(node,future,timeout_sec=.5)
        if future.done() and future.result().success:
            actual = future.result().state.pose.position
            reset_error = math.hypot(actual.x-start_x,actual.y-start_y)
            reset_measurements.append({'x':actual.x,'y':actual.y,'error_m':reset_error})
            consecutive_in_tolerance = consecutive_in_tolerance+1 if reset_error<=.05 else 0
            if consecutive_in_tolerance>=3:
                break
        wait_deadline=time.monotonic()+.1
        while time.monotonic()<wait_deadline:
            rclpy.spin_once(node,timeout_sec=.02)
    if consecutive_in_tolerance<3:
        raise RuntimeError('technical invalidity: measured reset position outside tolerance over bounded fresh-state window')
    initial = PoseWithCovarianceStamped()
    initial.header.frame_id = 'map'
    initial.header.stamp = node.get_clock().now().to_msg()
    initial.pose.pose = reset.state.pose
    initial.pose.covariance[0] = initial.pose.covariance[7] = .04
    initial.pose.covariance[35] = .04
    pose_pub.publish(initial)
    # Allow actual AMCL/scan updates following the independently sampled reset.
    reset_settle_deadline = time.monotonic()+3
    while time.monotonic()<reset_settle_deadline:
        rclpy.spin_once(node,timeout_sec=.1)
    localization_parameter_results = []
    if args.family == 'localization':
        parameters = node.create_client(SetParameters, '/amcl/set_parameters')
        if not parameters.wait_for_service(timeout_sec=10):
            raise RuntimeError('technical invalidity: AMCL parameter service unavailable')
        request = SetParameters.Request()
        request.parameters = [p.to_parameter_msg() for p in [Parameter('max_beams',value=5), Parameter('z_hit',value=.01), Parameter('z_rand',value=.99), Parameter('update_min_d',value=.01), Parameter('update_min_a',value=.01)]]
        future = parameters.call_async(request)
        rclpy.spin_until_future_complete(node,future,timeout_sec=10)
        if not future.done() or not all(r.successful for r in future.result().results):
            raise RuntimeError('technical invalidity: declared localization sensor model intervention failed')
        localization_parameter_results = [r.successful for r in future.result().results]

    if args.family in ("obstacle", "dynamic_env"):
        spawn = node.create_client(SpawnEntity, "/spawn_entity")
        if not spawn.wait_for_service(timeout_sec=10):
            raise RuntimeError("technical invalidity: obstacle spawn unavailable")
        req = SpawnEntity.Request()
        req.name = "hexar_intervention"
        req.xml = '<sdf version="1.6"><model name="hexar_intervention"><static>true</static><link name="body"><collision name="collision"><geometry><box><size>0.55 0.65 1.2</size></box></geometry></collision><visual name="visual"><geometry><box><size>0.55 0.65 1.2</size></box></geometry></visual></link></model></sdf>'
        req.initial_pose.position.x = target_x if args.family == "obstacle" else (start_x+target_x)/2
        req.initial_pose.position.y = target_y if args.family == "obstacle" else (start_y+target_y)/2
        req.initial_pose.position.z = .6
        req.initial_pose.orientation.w = 1.
        future = spawn.call_async(req)
        rclpy.spin_until_future_complete(node, future, timeout_sec=15)
        if not future.done() or not future.result().success:
            raise RuntimeError("technical invalidity: intervention spawn failed")
    charging.publish(Bool(data=args.family == "charging"))
    joystick.publish(Bool(data=args.family == "manual_joystick"))
    task = {"task_id": "independently-generated-navigation", "instruction": "go to the kitchen", "task_status": "running", "task_error_msg": "",
            "skill_sequence": [{"skill": "navigate_to_zone", "params": {"location": "kitchen"}, "status": "running", "error_msg": ""}]}
    subscription_deadline = time.monotonic() + 10
    while not task_pub.get_subscription_count() and time.monotonic() < subscription_deadline:
        rclpy.spin_once(node, timeout_sec=.1)
    if not task_pub.get_subscription_count():
        raise RuntimeError("technical invalidity: task recorder unavailable")
    task_pub.publish(String(data=json.dumps(task)))
    goal = NavigateToPose.Goal()
    goal.pose.header.frame_id = "map"
    goal.pose.header.stamp = node.get_clock().now().to_msg()
    goal.pose.pose.position.x, goal.pose.pose.position.y = target_x, target_y
    goal.pose.pose.orientation.z = math.sin(sampling['goal_yaw']/2)
    goal.pose.pose.orientation.w = math.cos(sampling['goal_yaw']/2)
    node.get_logger().info("SkillNavigateToZone received a new goal")
    if not goal_pub.get_subscription_count():
        goal_receipt_deadline = time.monotonic()+10
        while not goal_pub.get_subscription_count() and time.monotonic()<goal_receipt_deadline:
            rclpy.spin_once(node,timeout_sec=.1)
    if not goal_pub.get_subscription_count():
        raise RuntimeError("technical invalidity: actual navigation-goal publisher has no recorder")
    goal_pub.publish(goal.pose)
    future = action.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, future, timeout_sec=15)
    handle = future.result() if future.done() else None
    if not handle or not handle.accepted:
        raise RuntimeError("technical invalidity: goal not accepted")
    result_future = handle.get_result_async()
    start = time.monotonic()
    localization_applied = False
    mover = node.create_client(SetEntityState, "/set_entity_state") if args.family == "dynamic_env" else None
    move_count = 0
    move_futures = []
    no_motion = node.create_client(Empty, "/request_nomotion_update") if args.family == "localization" else None
    no_motion_futures = []
    no_motion_last = -1
    while not result_future.done() and time.monotonic() - start < args.timeout:
        elapsed = time.monotonic() - start
        charging.publish(Bool(data=args.family == "charging"))
        joystick.publish(Bool(data=args.family == "manual_joystick"))
        if args.family == "manual_joystick":
            joy_vel.publish(Twist()) # actual arbitration locks autonomous commands and holds still
        if args.family == "localization" and elapsed > 2 and not localization_applied:
            msg = PoseWithCovarianceStamped()
            msg.header.frame_id = "map"
            msg.header.stamp = node.get_clock().now().to_msg()
            msg.pose.pose.position.x = start_x + rng.uniform(-.3, .3)
            msg.pose.pose.position.y = start_y + rng.uniform(-.3, .3)
            msg.pose.pose.orientation.w = 1.
            msg.pose.covariance[0] = msg.pose.covariance[7] = 1.0
            msg.pose.covariance[35] = .5
            pose_pub.publish(msg)
            localization_applied = True
        if no_motion and no_motion.service_is_ready() and int(elapsed*4) > no_motion_last:
            no_motion_futures.append(no_motion.call_async(Empty.Request()))
            no_motion_last = int(elapsed*4)
        if mover and mover.service_is_ready() and int(elapsed * 2) > move_count:
            request = SetEntityState.Request()
            request.state = EntityState()
            request.state.name = "hexar_intervention"
            request.state.pose.position.x = (start_x+target_x)/2
            request.state.pose.position.y = (start_y+target_y)/2 + .8 * math.sin(elapsed)
            request.state.pose.position.z = .6
            request.state.pose.orientation.w = 1.
            move_futures.append(mover.call_async(request))
            move_count = int(elapsed * 2)
        rclpy.spin_once(node, timeout_sec=.1)
    timed_out = not result_future.done()
    if timed_out:
        cancel_future = handle.cancel_goal_async()
        rclpy.spin_until_future_complete(node, cancel_future, timeout_sec=10)
        rclpy.spin_until_future_complete(node, result_future, timeout_sec=10)
    result = result_future.result() if result_future.done() else None
    status = None if result is None else result.status
    succeeded = status == GoalStatus.STATUS_SUCCEEDED
    task["task_status"] = "succeeded" if succeeded else "failed"
    task["skill_sequence"][0]["status"] = "succeeded" if succeeded else "failed"
    task["skill_sequence"][0]["error_msg"] = "The skill has timed out" if timed_out else ("" if succeeded else "The skill has been aborted")
    task_pub.publish(String(data=json.dumps(task)))
    node.get_logger().info(f"NavigateToZone action server returned code: {status or 0}")
    if succeeded:
        node.get_logger().info("Skill completed successfully")
    for _ in range(10):
        rclpy.spin_once(node, timeout_sec=.1)
    report = {"schema": "hexar-development-episode-runtime/v1", "phase": "development_only", "family_hidden": args.family,
              "sampling_hidden": sampling, "measured_reset_error_m": reset_error, "reset_measurements_hidden": reset_measurements,
              "localization_parameters_accepted": localization_parameter_results,
              "nomotion_update_responses": sum(f.done() and f.result() is not None for f in no_motion_futures),
              "seed_hidden": args.seed, "goal_hidden": [target_x, target_y], "accepted": True, "terminal_action_status": status,
              "timeout": timed_out, "localization_intervention_applied": localization_applied,
              "dynamic_move_requests": len(move_futures),
              "dynamic_moves_confirmed_success": sum(f.done() and f.result() is not None and f.result().success for f in move_futures),
              "dynamic_moves_confirmed_failure": sum(f.done() and f.result() is not None and not f.result().success for f in move_futures),
              "dynamic_moves_unresolved": sum(not f.done() for f in move_futures), "semantic_outputs_generated": False,
              "qualification_complete": False}
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
