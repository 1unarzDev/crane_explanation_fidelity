"""Development-only live ROS integrity probe; never supplies method evidence."""
import argparse
import json
import time
from pathlib import Path


def main():
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from rosgraph_msgs.msg import Clock
    from sensor_msgs.msg import LaserScan
    from nav_msgs.msg import Odometry
    from lifecycle_msgs.srv import GetState
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=30)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rclpy.init()
    node = Node("hexar_acquisition_integrity_probe")
    samples = {"clock": 0, "scan": 0, "odom": 0}
    clock_ns = []
    def clock_cb(msg):
        samples["clock"] += 1
        clock_ns.append(msg.clock.sec * 10**9 + msg.clock.nanosec)
    def sample(topic):
        def callback(msg):
            samples[topic] += 1
        return callback
    node.create_subscription(Clock, "/clock", clock_cb, qos_profile_sensor_data)
    node.create_subscription(LaserScan, "/scan_raw", sample("scan"), qos_profile_sensor_data)
    node.create_subscription(Odometry, "/mobile_base_controller/odom", sample("odom"), qos_profile_sensor_data)
    start = time.monotonic()
    while time.monotonic() - start < args.duration:
        rclpy.spin_once(node, timeout_sec=0.2)
    states = {}
    for name in ("amcl", "planner_server", "controller_server", "bt_navigator"):
        client = node.create_client(GetState, f"/{name}/get_state")
        if client.wait_for_service(timeout_sec=3):
            future = client.call_async(GetState.Request())
            rclpy.spin_until_future_complete(node, future, timeout_sec=3)
            result = future.result() if future.done() else None
            states[name] = None if result is None else {"id": result.current_state.id, "label": result.current_state.label}
        else:
            states[name] = None
    report = {"schema": "hexar-live-runtime-probe/v1", "phase": "development_only",
              "samples": samples, "clock_advancing": bool(clock_ns) and clock_ns[-1] > clock_ns[0],
              "lifecycle": states, "topics": dict(node.get_topic_names_and_types()),
              "qualified": all(samples.values()) and bool(clock_ns) and clock_ns[-1] > clock_ns[0] and
                           all(state and state["id"] == 3 for state in states.values())}
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    node.destroy_node()
    rclpy.shutdown()
    return 0 if report["qualified"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
