using System;
using System.Globalization;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Sim.Controllers {
    /// <summary>Opt-in planar initial configuration, before scene Start and physics.</summary>
    internal static class RoboBoatInitialPose {
        internal const string Option = "--crane-roboboat-start-pose";
        internal const string SceneName = "Roboboat Course";

        internal static bool TryParse(string[] args, out Vector3 rosPose) {
            rosPose = Vector3.zero;
            int index = Array.IndexOf(args, Option);
            if (index < 0) return false;
            if (Array.LastIndexOf(args, Option) != index || index + 1 >= args.Length)
                throw new ArgumentException("Start pose must be supplied exactly once as x,y,yaw.");
            string[] values = args[index + 1].Split(',');
            if (values.Length != 3)
                throw new ArgumentException("Start pose requires ROS odom x,y,yaw in metres/radians.");
            for (int i = 0; i < 3; i++) {
                if (!float.TryParse(values[i], NumberStyles.Float, CultureInfo.InvariantCulture,
                        out float value) || float.IsNaN(value) || float.IsInfinity(value))
                    throw new ArgumentException("Start pose values must be finite invariant numbers.");
                rosPose[i] = value;
            }
            if (Math.Abs(rosPose.z) > Mathf.PI)
                throw new ArgumentException("Start yaw must use the canonical [-pi,pi] interval.");
            return true;
        }

        internal static Vector3 Position(Vector3 rosPose, float height) =>
            new(-rosPose.y, height, rosPose.x);

        // Publisher maps Unity (z,-x,y) to FLU and corrects the boat's local bow by -90deg.
        internal static Quaternion Rotation(float rosYaw) =>
            Quaternion.Euler(0f, 90f - rosYaw * Mathf.Rad2Deg, 0f);

        internal static void Apply(Component body, Vector3 rosPose) {
            if (body == null) throw new ArgumentNullException(nameof(body));
            Vector3 position = Position(rosPose, body.transform.position.y);
            Quaternion rotation = Rotation(rosPose.z);
            if (body is ArticulationBody articulation) {
                if (!articulation.isRoot)
                    throw new ArgumentException("Start pose requires the root articulation body.");
                // Before the first physics update, also set the scene transform explicitly.
                // TeleportRoot alone does not guarantee the immediate transform readback.
                articulation.transform.SetPositionAndRotation(position, rotation);
                articulation.TeleportRoot(position, rotation);
                articulation.linearVelocity = Vector3.zero;
                articulation.angularVelocity = Vector3.zero;
            }
            else if (body is Rigidbody rigidbody) {
                rigidbody.position = position;
                rigidbody.rotation = rotation;
                rigidbody.linearVelocity = Vector3.zero;
                rigidbody.angularVelocity = Vector3.zero;
            }
            else throw new ArgumentException("Start pose requires a supported physics body.");
            Physics.SyncTransforms();
        }

        internal static Component FindBody(Scene scene) {
            if (!scene.name.Equals(SceneName, StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException("Start-pose override is restricted to the RoboBoat course.");
            OmniXController selected = null;
            foreach (GameObject root in scene.GetRootGameObjects()) {
                foreach (OmniXController candidate in root.GetComponentsInChildren<OmniXController>()) {
                    if (!candidate.isActiveAndEnabled) continue;
                    if (selected != null)
                        throw new InvalidOperationException("Exactly one active RoboBoat controller required.");
                    selected = candidate;
                }
            }
            if (selected == null)
                throw new MissingReferenceException("No active RoboBoat controller in requested scene.");
            foreach (ArticulationBody body in selected.GetComponentsInParent<ArticulationBody>())
                if (body.isRoot) return body;
            Rigidbody rigidbody = selected.GetComponentInParent<Rigidbody>();
            if (rigidbody != null) return rigidbody;
            throw new MissingReferenceException("RoboBoat root physics body missing.");
        }
    }

    internal static class RoboBoatInitialPoseBootstrap {
        private static Vector3 pose;

        [Serializable] private sealed class Receipt {
            public string scene;
            public string body;
            public string bodyType;
            public Vector3 requestedRosXYAndYaw;
            public Vector3 observedUnityPosition;
            public Quaternion observedUnityRotation;
            public string phase = "sceneLoaded-before-Start-and-physics";
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void Install() {
            // No subscription or state mutation when the explicit option is absent.
            SceneManager.sceneLoaded -= OnSceneLoaded;
            try {
                if (!RoboBoatInitialPose.TryParse(Environment.GetCommandLineArgs(), out pose)) return;
            }
            catch (ArgumentException error) {
                Debug.LogException(error);
                Application.Quit(2);
                return;
            }
            SceneManager.sceneLoaded += OnSceneLoaded;
        }

        private static void OnSceneLoaded(Scene scene, LoadSceneMode mode) {
            // The launcher may load a transient build-index scene before the target.
            if (!scene.name.Equals(RoboBoatInitialPose.SceneName, StringComparison.OrdinalIgnoreCase)) return;
            try {
                Component body = RoboBoatInitialPose.FindBody(scene);
                RoboBoatInitialPose.Apply(body, pose);
                Debug.Log("CRANE_ROBOBOAT_INITIAL_POSE " + JsonUtility.ToJson(new Receipt {
                    scene = scene.name, body = body.name, bodyType = body.GetType().Name,
                    requestedRosXYAndYaw = pose, observedUnityPosition = body.transform.position,
                    observedUnityRotation = body.transform.rotation
                }));
            }
            catch (Exception error) {
                Debug.LogException(error);
                Application.Quit(2);
            }
        }
    }
}
