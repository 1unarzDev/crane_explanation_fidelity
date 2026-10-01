using UnityEngine;

// Useful for testing physical boat interfaces like ros2_control
namespace Sim.Controllers {
    public interface IControllerBase {
        void SetMotion(Vector3 linear, Vector3 angular);
    }
}