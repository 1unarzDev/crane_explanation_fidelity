using UnityEngine;
using System;
using Sim.Utils;

namespace Sim.Actuators.Motors {
    public interface IMotorConfig {
        MotorControlMode controlMode { get; }
        Axis rotationAxis { get; }
        Pid pid { get; }
        float maxTorque { get; }
        float maxAngularVelocity { get; }
        float torqueK { get; }
        float minAngle { get; }
        float maxAngle { get; }
    }
}
