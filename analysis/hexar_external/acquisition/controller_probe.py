"""Observe actual mux parameters and graph; no scenario/semantic inputs.

Snapshots are software runtime observations. They do not assert physical causes,
continuous wiring, delivered messages or applied wheel torque.
"""
import hashlib
import json
from pathlib import Path


def capture(node):
    from rcl_interfaces.srv import ListParameters, GetParameters
    from rcl_interfaces.msg import ParameterType
    import rclpy
    list_client=node.create_client(ListParameters,'/twist_mux/list_parameters')
    get_client=node.create_client(GetParameters,'/twist_mux/get_parameters')
    if not list_client.wait_for_service(timeout_sec=5) or not get_client.wait_for_service(timeout_sec=5):
        raise RuntimeError('observed mux parameter services unavailable')
    listing=ListParameters.Request();listing.prefixes=['topics','locks','use_sim_time'];listing.depth=0
    future=list_client.call_async(listing);rclpy.spin_until_future_complete(node,future,timeout_sec=5)
    if not future.done() or future.result() is None:
        raise RuntimeError('observed mux parameter listing unavailable')
    names=sorted(future.result().result.names)
    if not names:raise RuntimeError('empty observed mux parameter set')
    request=GetParameters.Request();request.names=names
    future=get_client.call_async(request);rclpy.spin_until_future_complete(node,future,timeout_sec=5)
    if not future.done() or future.result() is None or len(future.result().values)!=len(names):
        raise RuntimeError('observed mux parameter values unavailable')
    fields={ParameterType.PARAMETER_BOOL:'bool_value',ParameterType.PARAMETER_INTEGER:'integer_value',
            ParameterType.PARAMETER_DOUBLE:'double_value',ParameterType.PARAMETER_STRING:'string_value'}
    parameters={}
    for name,value in zip(names,future.result().values):
        if value.type not in fields:raise RuntimeError('unexpected mux parameter scalar type')
        parameters[name]=getattr(value,fields[value.type])
    nodes=node.get_node_names_and_namespaces()
    if ('twist_mux','/') not in nodes:raise RuntimeError('observed mux graph node unavailable')
    subscribers={name:types for name,types in node.get_subscriber_names_and_types_by_node('twist_mux','/')}
    publishers={name:types for name,types in node.get_publisher_names_and_types_by_node('twist_mux','/')}
    output='/mobile_base_controller/cmd_vel_unstamped'
    receivers=[dict(node_name=info.node_name,node_namespace=info.node_namespace,topic_type=info.topic_type)
               for info in node.get_subscriptions_info_by_topic(output)]
    stamp=node.get_clock().now().to_msg()
    snapshot=dict(schema='hexar-observed-controller-context/v1',
        stamp=dict(sec=int(stamp.sec),nanosec=int(stamp.nanosec)),node='/twist_mux',
        parameters=parameters,subscribers=subscribers,publishers=publishers,output_receivers=receivers,
        scope='acknowledged parameter service and ROS graph observations at this stamp; not proof of continuous delivery or physical causation')
    required={'topics.navigation.topic':'cmd_vel','topics.navigation.priority':10,
              'locks.joystick.topic':'joy_priority','locks.joystick.priority':100,
              'locks.charging.topic':'power/is_charging','locks.charging.priority':210,'use_sim_time':True}
    mismatches=[k for k,v in required.items() if parameters.get(k)!=v]
    graph_required={'/cmd_vel':'geometry_msgs/msg/Twist','/joy_priority':'std_msgs/msg/Bool',
                    '/power/is_charging':'std_msgs/msg/Bool'}
    missing=[k for k,t in graph_required.items() if t not in subscribers.get(k,[])]
    if 'geometry_msgs/msg/Twist' not in publishers.get(output,[]):missing.append(output+' publisher')
    if not any(r['topic_type']=='geometry_msgs/msg/Twist' for r in receivers):missing.append(output+' receiver')
    return snapshot,dict(schema='hexar-controller-probe-technical-review/v1',
        candidate_integrity=not mismatches and not missing,parameter_mismatches=mismatches,graph_missing=missing,
        probe_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        semantic_method_outputs_used=False,physical_cause_claim_qualified=False)


def main():
    import argparse
    import rclpy
    from rclpy.node import Node
    from rclpy.parameter import Parameter
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    rclpy.init();node=Node('hexar_controller_context_observer')
    node.set_parameters([Parameter('use_sim_time',value=True)])
    # Allow the observer's simulated clock to receive native clock messages.
    for _ in range(10):rclpy.spin_once(node,timeout_sec=.1)
    snapshot,review=capture(node)
    with args.output.open('x') as f:json.dump(dict(snapshot=snapshot,technical_review=review),f,indent=2);f.write('\n')
    node.destroy_node();rclpy.shutdown()
    return 0 if review['candidate_integrity'] else 1


if __name__=='__main__':raise SystemExit(main())
