using UnityEngine;

namespace Sim.Utils {
    public class RigidbodyAdapter : IPhysicsBody {
        private Rigidbody rb;

        public RigidbodyAdapter(Rigidbody rb) {
            this.rb = rb;
        }

        public Vector3 position { get => rb.position; set => rb.position = value; }
        public Vector3 centerOfMass { get => rb.centerOfMass; set => rb.centerOfMass = value; }
        public Quaternion rotation { get => rb.rotation; set => rb.rotation = value; }
        public Transform transform { get => rb.transform; }
        public Vector3 linearVelocity { get => rb.linearVelocity; set => rb.linearVelocity = value; }
        public Vector3 angularVelocity { get => rb.angularVelocity; set => rb.angularVelocity = value; }
        public Vector3 inertiaTensor { get => rb.inertiaTensor; set => rb.inertiaTensor = value; }
        public Quaternion inertiaTensorRotation { get => rb.inertiaTensorRotation; set => rb.inertiaTensorRotation = value; }
        public Vector3 GetAccumulatedTorque(float step)
            => rb.GetAccumulatedTorque(step);
        public Vector3 GetAccumulatedTorque()
            => rb.GetAccumulatedTorque();

        public float maxLinearVelocity { get => rb.maxLinearVelocity; set => rb.maxLinearVelocity = value; }
        public float maxAngularVelocity { get => rb.maxAngularVelocity; set => rb.maxAngularVelocity = value; }

        public void AddForce(Vector3 force, ForceMode mode = ForceMode.Force)
            => rb.AddForce(force, mode);

        public void AddRelativeForce(Vector3 force, ForceMode mode = ForceMode.Force)
            => rb.AddRelativeForce(force, mode);

        public void AddForceAtPosition(Vector3 force, Vector3 position, ForceMode mode = ForceMode.Force)
            => rb.AddForceAtPosition(force, position, mode);

        public void AddTorque(Vector3 torque, ForceMode mode = ForceMode.Force)
            => rb.AddTorque(torque, mode);

        public void AddRelativeTorque(Vector3 torque, ForceMode mode = ForceMode.Force)
            => rb.AddRelativeTorque(torque, mode);
    }
}
