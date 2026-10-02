"""Wait for live Nav2 lifecycle activation, without inspecting semantic outcomes."""
import argparse
import time
import rclpy
from rclpy.node import Node
from lifecycle_msgs.srv import GetState

ap = argparse.ArgumentParser()
ap.add_argument('--timeout', type=float, default=90)
args = ap.parse_args()
rclpy.init()
node = Node('hexar_wait_for_acquisition')
clients = {name: node.create_client(GetState, f'/{name}/get_state') for name in ('amcl', 'controller_server', 'planner_server', 'bt_navigator')}
end = time.monotonic() + args.timeout
while time.monotonic() < end:
    states = {}
    for name, client in clients.items():
        if client.service_is_ready():
            future = client.call_async(GetState.Request())
            rclpy.spin_until_future_complete(node, future, timeout_sec=1)
            states[name] = future.result().current_state.id if future.done() and future.result() else None
    if len(states) == len(clients) and all(v == 3 for v in states.values()):
        print('Live Nav2 lifecycle activation verified:', states)
        node.destroy_node()
        rclpy.shutdown()
        raise SystemExit(0)
    rclpy.spin_once(node, timeout_sec=.5)
print('TECHNICAL_INVALIDITY: lifecycle activation timeout', states)
node.destroy_node()
rclpy.shutdown()
raise SystemExit(1)
