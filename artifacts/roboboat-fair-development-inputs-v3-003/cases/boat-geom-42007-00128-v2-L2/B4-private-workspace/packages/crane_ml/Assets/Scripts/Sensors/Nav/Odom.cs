using UnityEngine;
using RosMessageTypes.Nav;
using RosMessageTypes.Geometry;
using Unity.Robotics.ROSTCPConnector.ROSGeometry;
using Sim.Utils;
using Sim.Utils.ROS;

namespace Sim.Sensors.Nav {
    public class Odom : MonoBehaviour, IROSSensor<OdometryMsg> {
        [SerializeField] private string topicName = "odometry";
        [SerializeField] private string frameId = "odom";
        [SerializeField] private float Hz = 50.0f;
        public ROSPublisher publisher { get; set; }

        private IPhysicsBody body;

        void OnValidate() {
            if (GetComponent<Rigidbody>() == null && GetComponent<ArticulationBody>() == null)
                Debug.LogWarning($"{name} should have either a Rigidbody or an ArticulationBody attached.");
        }

        void Awake() {
            var rb = GetComponent<Rigidbody>();
            var ab = GetComponent<ArticulationBody>();

            if (rb != null) body = new RigidbodyAdapter(rb);
            else if (ab != null) body = new ArticulationBodyAdapter(ab);
            else throw new MissingComponentException($"{name} requires a Rigidbody or ArticulationBody!");

            publisher = gameObject.AddComponent<ROSPublisher>();
        }

        public OdometryMsg CreateMessage() {
            OdometryMsg msg = new();

            Vector3 pos = transform.position;
            msg.pose.pose.position = new PointMsg {
                x = pos.z,
                y = -pos.x,
                z = pos.y
            };

            msg.pose.pose.orientation = body.transform.rotation.To<FLU>();

            Vector3 localVel = transform.InverseTransformDirection(body.linearVelocity);
            msg.twist.twist.linear.x = localVel.z;
            msg.twist.twist.linear.y = -localVel.x;
            msg.twist.twist.linear.z = localVel.y;

            msg.twist.twist.angular.x = 0;
            msg.twist.twist.angular.y = 0;
            msg.twist.twist.angular.z = -body.angularVelocity.y;

            msg.header = publisher.CreateHeader();

            return msg;
        }

        void Start() {
            publisher.Initialize(topicName, frameId, CreateMessage, Hz);
        }
    }
}
