using UnityEngine;

namespace Sim.Utils {
    public interface IPhysicsBody {
        Vector3 position { get; set; }
        Quaternion rotation { get; set; }
        Transform transform { get; }
        Vector3 centerOfMass { get; set; }
        Vector3 linearVelocity { get; set; }
        Vector3 angularVelocity { get; set; }
        Vector3 inertiaTensor { get; set; }
        Quaternion inertiaTensorRotation { get; set; }
        Vector3 GetAccumulatedTorque();
        Vector3 GetAccumulatedTorque(float step);
        float maxLinearVelocity { get; set; }
        float maxAngularVelocity { get; set; }

        void AddForce(Vector3 force, ForceMode mode = ForceMode.Force);
        void AddRelativeForce(Vector3 force, ForceMode mode = ForceMode.Force);
        void AddForceAtPosition(Vector3 force, Vector3 position, ForceMode mode = ForceMode.Force);
        void AddTorque(Vector3 torque, ForceMode mode = ForceMode.Force);
        void AddRelativeTorque(Vector3 torque, ForceMode mode = ForceMode.Force);
    }
}
