using UnityEngine;
using System;
using Sim.Utils;
using UnityEngine.Rendering.HighDefinition;

namespace Sim.Actuators.Motors {
    [CreateAssetMenu(menuName = "Motors/ThrusterConfig")]
    public class ThrusterConfig : ScriptableObject, IMotorConfig {
        public float minAngle { get => float.NegativeInfinity; set { } }
        public float maxAngle { get => float.PositiveInfinity; set { } }
        public Pid pid { get; set; } = null;

        [field: SerializeField] public float thrustK { get; set; } = 4.0f;
        [field: SerializeField] public float backK { get; set; } = 0.8f;
        [field: SerializeField] public float height { get; set; } = 0.08f;
        [field: SerializeField] public MotorControlMode controlMode { get; set; } = MotorControlMode.Torque;
        [field: SerializeField] public Axis rotationAxis { get; set; } = Axis.Y;
        [field: SerializeField, Tooltip("Nm")] public float maxTorque { get; set; } = 1.3f;
        [field: SerializeField, Tooltip("rad/s, Caps angular velocity (vital to get correct for controller to work)")] public float maxAngularVelocity { get; set; } = 200f;
        [field: SerializeField, Tooltip("Torque Responsiveness"), Range(0.0f, 1.0f)] public float torqueK { get; set; } = 1.0f;

        public float GetMaxThrust() => (maxAngularVelocity * maxAngularVelocity) * thrustK;
        public float GetMaxBackThrust() => GetMaxThrust() * backK;
        public float GetMaxCommand() => controlMode switch {
            MotorControlMode.Torque => maxTorque,
            MotorControlMode.Velocity => maxAngularVelocity,
            MotorControlMode.Position => maxAngle,
            _ => 0.0f
        };
        public float GetMinCommand() => controlMode switch {
            MotorControlMode.Torque => -maxTorque,
            MotorControlMode.Velocity => -maxAngularVelocity,
            MotorControlMode.Position => minAngle,
            _ => 0.0f
        };
    }
}
