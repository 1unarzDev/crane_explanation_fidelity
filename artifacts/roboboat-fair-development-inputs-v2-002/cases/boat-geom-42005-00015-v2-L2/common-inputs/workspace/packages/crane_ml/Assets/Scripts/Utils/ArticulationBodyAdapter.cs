using UnityEngine;

namespace Sim.Utils {
    public class ArticulationBodyAdapter : IPhysicsBody {
        private ArticulationBody ab;

        public ArticulationBodyAdapter(ArticulationBody ab) {
            this.ab = ab;
        }

        public Vector3 position {
            get => ab.transform.position;
            set => ab.TeleportRoot(value, ab.transform.rotation);
        }
        public Quaternion rotation {
            get => ab.transform.rotation;
            set => ab.TeleportRoot(ab.transform.position, value);
        }
        public Transform transform { get => ab.transform; }
        public Vector3 centerOfMass { get => ab.centerOfMass; set => ab.centerOfMass = value; }
        public Vector3 linearVelocity { get => ab.linearVelocity; set => ab.linearVelocity = value; }
        public Vector3 angularVelocity { get => ab.angularVelocity; set => ab.angularVelocity = value; }
        public Vector3 inertiaTensor { get => ab.inertiaTensor; set => ab.inertiaTensor = value; }
        public Quaternion inertiaTensorRotation { get => ab.inertiaTensorRotation; set => ab.inertiaTensorRotation = value; }
        public Vector3 GetAccumulatedTorque(float step)
            => ab.GetAccumulatedTorque(step);
        public Vector3 GetAccumulatedTorque()
            => ab.GetAccumulatedTorque();
        public float maxLinearVelocity { get => ab.maxLinearVelocity; set => ab.maxLinearVelocity = value; }
        public float maxAngularVelocity { get => ab.maxAngularVelocity; set => ab.maxAngularVelocity = value; }

        public void AddForce(Vector3 force, ForceMode mode = ForceMode.Force)
            => ab.AddForce(force, mode);

        public void AddRelativeForce(Vector3 force, ForceMode mode = ForceMode.Force)
            => ab.AddRelativeForce(force, mode);

        public void AddForceAtPosition(Vector3 force, Vector3 position, ForceMode mode = ForceMode.Force)
            => ab.AddForceAtPosition(force, position, mode);

        public void AddTorque(Vector3 torque, ForceMode mode = ForceMode.Force)
            => ab.AddTorque(torque, mode);

        public void AddRelativeTorque(Vector3 torque, ForceMode mode = ForceMode.Force)
            => ab.AddRelativeTorque(torque, mode);
    }
}
