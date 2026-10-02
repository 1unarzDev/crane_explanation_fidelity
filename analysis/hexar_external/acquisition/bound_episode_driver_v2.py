"""Versioned bound navigation driver; unchanged physics and explicit acquisition provenance."""
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
    from rcl_interfaces.srv import SetParameters,GetParameters
    from std_srvs.srv import Empty
    from sampling import sample
    from reset_geometry import review as review_reset
    from scenario_geometry import trajectory,position as trajectory_position
    from gazebo_msgs.msg import EntityState
    from action_msgs.msg import GoalStatus
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=("success", "obstacle", "dynamic_env", "localization", "charging", "manual_joystick"), required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--timeout", type=float, default=75)
    ap.add_argument("--acquisition-phase", choices=("development_adapter_qualification", "raw_confirmation"), required=True)
    ap.add_argument("--acquisition-binding", required=True)
    args = ap.parse_args()
    if len(args.acquisition_binding) != 64 or any(c not in "0123456789abcdef" for c in args.acquisition_binding):
        ap.error("exact acquisition binding hash required")
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
    event_pub = node.create_publisher(String, '/hexar_acquisition/navigation_event', 10)
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
    reset_heading_error = float('inf')
    while time.monotonic() < reset_deadline:
        future = ground_truth.call_async(verify)
        rclpy.spin_until_future_complete(node,future,timeout_sec=.5)
        if future.done() and future.result().success:
            actual = future.result().state.pose
            p,q = actual.position,actual.orientation
            measurement=review_reset((p.x,p.y,p.z),(q.x,q.y,q.z,q.w),(start_x,start_y),sampling['start_yaw'])
            reset_error=measurement['error_m'];reset_heading_error=measurement['heading_error_rad']
            reset_measurements.append(measurement)
            consecutive_in_tolerance = consecutive_in_tolerance+1 if measurement['in_tolerance'] else 0
            if consecutive_in_tolerance>=3:
                break
        wait_deadline=time.monotonic()+.1
        while time.monotonic()<wait_deadline:
            rclpy.spin_once(node,timeout_sec=.02)
    if consecutive_in_tolerance<3:
        raise RuntimeError('technical invalidity: measured reset position/heading outside tolerance over bounded fresh-state window')
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
    localization_parameter_observations = []
    if args.family == 'localization':
        parameters = node.create_client(SetParameters, '/amcl/set_parameters')
        if not parameters.wait_for_service(timeout_sec=10):
            raise RuntimeError('technical invalidity: AMCL parameter service unavailable')
        request = SetParameters.Request()
        request.parameters = [p.to_parameter_msg() for p in [Parameter('max_beams',value=5), Parameter('z_hit',value=.01), Parameter('z_rand',value=.99), Parameter('update_min_d',value=.01), Parameter('update_min_a',value=.01)]]
        future = parameters.call_async(request)
        rclpy.spin_until_future_complete(node,future,timeout_sec=10)
        if not future.done() or len(future.result().results)!=len(request.parameters) or not all(r.successful for r in future.result().results):
            raise RuntimeError('technical invalidity: declared localization sensor model intervention failed')
        localization_parameter_results = [r.successful for r in future.result().results]
        readback=node.create_client(GetParameters,'/amcl/get_parameters')
        if not readback.wait_for_service(timeout_sec=10):
            raise RuntimeError('technical invalidity: AMCL intervention readback unavailable')
        get=GetParameters.Request();get.names=[p.name for p in request.parameters]
        fetched=readback.call_async(get);rclpy.spin_until_future_complete(node,fetched,timeout_sec=10)
        if not fetched.done() or len(fetched.result().values)!=len(request.parameters) or any(actual!=expected.value for actual,expected in zip(fetched.result().values,request.parameters)):
            raise RuntimeError('technical invalidity: AMCL intervention readback differs from requested configuration')
        localization_parameter_observations=[dict(name=name,type=value.type,integer_value=value.integer_value,double_value=value.double_value) for name,value in zip(get.names,fetched.result().values)]

    intervention_observations=[]
    dynamic_profile=trajectory(args.seed,(start_x,start_y),(target_x,target_y)) if args.family=='dynamic_env' else None
    trajectory_start_ns=None
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
        intervention_verify=GetEntityState.Request();intervention_verify.name='hexar_intervention'
        def observe_intervention(requested_xyz,stage):
            observed=ground_truth.call_async(intervention_verify)
            rclpy.spin_until_future_complete(node,observed,timeout_sec=2)
            if not observed.done() or not observed.result().success:
                raise RuntimeError('technical invalidity: intervention state observation unavailable')
            actual=observed.result().state.pose.position
            xyz=[actual.x,actual.y,actual.z]
            if any(not math.isfinite(v) for v in xyz) or math.dist(xyz,requested_xyz)>.05:
                raise RuntimeError('technical invalidity: observed intervention position differs from requested pose')
            intervention_observations.append(dict(stage=stage,requested_xyz=requested_xyz,observed_xyz=xyz,
                observed_sim_stamp_ns=node.get_clock().now().nanoseconds,
                source='Gazebo GetEntityState world pose; technical-only hidden intervention observation'))
        observe_intervention([req.initial_pose.position.x,req.initial_pose.position.y,req.initial_pose.position.z],'spawn')
        if dynamic_profile:
            # Deliver and measure the moving-object configuration before goal
            # acceptance, avoiding exclusions driven by early navigation results.
            trajectory_start_ns=node.get_clock().now().nanoseconds
            for target_elapsed in (0.,.5,1.):
                deadline=time.monotonic()+5
                while (node.get_clock().now().nanoseconds-trajectory_start_ns)/1e9<target_elapsed and time.monotonic()<deadline:
                    rclpy.spin_once(node,timeout_sec=.05)
                elapsed_sim=(node.get_clock().now().nanoseconds-trajectory_start_ns)/1e9
                if elapsed_sim<target_elapsed:
                    raise RuntimeError('technical invalidity: native simulation clock stalled during dynamic prelude')
                xyz=trajectory_position(dynamic_profile,elapsed_sim)
                move=SetEntityState.Request();move.state.name='hexar_intervention'
                move.state.pose.position.x,move.state.pose.position.y,move.state.pose.position.z=xyz
                move.state.pose.orientation.w=1.
                observed_move=reposition.call_async(move)
                rclpy.spin_until_future_complete(node,observed_move,timeout_sec=2)
                if not observed_move.done() or not observed_move.result().success:
                    raise RuntimeError('technical invalidity: dynamic prelude motion was not accepted')
                observe_intervention(xyz,'dynamic_prelude')
    indicator_consumers={}
    discovery_deadline=time.monotonic()+10
    for topic in ('/power/is_charging','/joy_priority'):
        consumers=[]
        while time.monotonic()<discovery_deadline:
            consumers=node.get_subscriptions_info_by_topic(topic)
            if any(info.node_name=='twist_mux' and info.topic_type=='std_msgs/msg/Bool' for info in consumers):break
            rclpy.spin_once(node,timeout_sec=.1)
        if not any(info.node_name=='twist_mux' and info.topic_type=='std_msgs/msg/Bool' for info in consumers):
            raise RuntimeError('technical invalidity: indicator has no observed actual twist_mux consumer')
        indicator_consumers[topic]=[dict(node_name=info.node_name,node_namespace=info.node_namespace,topic_type=info.topic_type) for info in consumers]
    # Publish the configured states before any navigation outcome can occur.
    for _ in range(3):
        charging.publish(Bool(data=args.family == 'charging'))
        joystick.publish(Bool(data=args.family == 'manual_joystick'))
        if args.family=='manual_joystick':joy_vel.publish(Twist())
        deadline=time.monotonic()+.1
        while time.monotonic()<deadline:rclpy.spin_once(node,timeout_sec=.02)
    task = {"task_id": "independently-generated-navigation", "instruction": "navigate to the requested map-frame pose", "task_status": "running", "task_error_msg": "",
            "skill_sequence": [{"skill": "navigate_to_zone", "params": {"location": "requested map-frame pose"}, "status": "running", "error_msg": ""}]}
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
    event_receipt_deadline = time.monotonic()+10
    while not event_pub.get_subscription_count() and time.monotonic()<event_receipt_deadline:
        rclpy.spin_once(node,timeout_sec=.1)
    if not event_pub.get_subscription_count():
        raise RuntimeError('technical invalidity: observed action-event recorder unavailable')
    future = action.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, future, timeout_sec=15)
    handle = future.result() if future.done() else None
    if not handle or not handle.accepted:
        raise RuntimeError("technical invalidity: goal not accepted")
    def execution_event(event, status=None):
        stamp = node.get_clock().now().to_msg()
        payload = {'schema':'hexar-observed-navigation-event/v1', 'event':event,
                   'stamp':{'sec':int(stamp.sec),'nanosec':int(stamp.nanosec)},
                   'goal_id_hex':bytes(handle.goal_id.uuid).hex(), 'status':status,
                   'scope':'driver observation of action protocol; not physical arrival'}
        event_pub.publish(String(data=json.dumps(payload)))
    # Observed acceptance/result events, never intended outcomes. Native ROS
    # stamps share the simulated clock with recorded stamped odometry.
    execution_event('accepted')
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
            xyz=trajectory_position(dynamic_profile,(node.get_clock().now().nanoseconds-trajectory_start_ns)/1e9)
            request.state.pose.position.x,request.state.pose.position.y,request.state.pose.position.z=xyz
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
    execution_event('terminal_result' if result is not None else 'terminal_result_unavailable', status)
    succeeded = status == GoalStatus.STATUS_SUCCEEDED
    task["task_status"] = "succeeded" if succeeded else "failed"
    task["skill_sequence"][0]["status"] = "succeeded" if succeeded else "failed"
    task["skill_sequence"][0]["error_msg"] = ("The skill has timed out" if timed_out else
        "" if succeeded else "The skill has been aborted" if status == GoalStatus.STATUS_ABORTED else
        "Navigation action was canceled" if status == GoalStatus.STATUS_CANCELED else "Terminal action result unavailable")
    task_pub.publish(String(data=json.dumps(task)))
    node.get_logger().info(f"NavigateToZone action server returned code: {status or 0}")
    if succeeded:
        node.get_logger().info("Skill completed successfully")
    for _ in range(10):
        rclpy.spin_once(node, timeout_sec=.1)
    report = {"schema": "hexar-bound-episode-runtime/v2", "phase": args.acquisition_phase,
              "acquisition_binding_sha256": args.acquisition_binding, "family_hidden": args.family,
              "sampling_hidden": sampling, "measured_reset_error_m": reset_error, "reset_measurements_hidden": reset_measurements,
              "measured_reset_heading_error_rad": reset_heading_error,
              "intervention_observations_hidden": intervention_observations,
              "dynamic_trajectory_hidden": dynamic_profile,
              "indicator_consumers_hidden": indicator_consumers,
              "indicator_prelude_publications_per_topic": 3,
              "localization_parameters_accepted": localization_parameter_results,
              "localization_parameters_observed_hidden": localization_parameter_observations,
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
