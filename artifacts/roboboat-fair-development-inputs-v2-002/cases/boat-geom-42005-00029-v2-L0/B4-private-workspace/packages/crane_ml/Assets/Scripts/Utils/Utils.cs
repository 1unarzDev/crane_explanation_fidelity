using System.Diagnostics;
using System.IO;
using System;
using UnityEngine;

namespace Sim.Utils {
    public class CommonUtils : MonoBehaviour {
        private string path = "Assets/Data/";

        // Called in Submerged.cs/GetSubmergedTriangles().
        // Retuns the normal vector of a triangle given its vertices.
        public static Vector3 GetFaceNormal(Vector3 A, Vector3 B, Vector3 C) {
            Vector3 normal = 0.5f * Vector3.Cross((B - A), (C - A));
            return normal;
        }

        public static Vector3 GetAveragePoint(Vector3[] vecs) {
            Vector3 tot = Vector3.zero;
            foreach (Vector3 v in vecs) {
                tot += v;
            }
            return tot / vecs.Length;
        }

        public static void DebugDrawTriangle(Vector3[] triangle, Color color) {
            UnityEngine.Debug.DrawLine(triangle[0], triangle[1], color);
            UnityEngine.Debug.DrawLine(triangle[0], triangle[2], color);
            UnityEngine.Debug.DrawLine(triangle[1], triangle[2], color);
        }

        // Using generics to logdata to a csv file. First parameter is file path,
        // second and third are the data to be logged.
        public static void LogDataToFile<T1, T2>(string filePath, T1 x, T2 y) {
            string data = $"{x},{y}";
            using (StreamWriter sw = File.AppendText(filePath)) {
                sw.WriteLine(data);
            }
        }

        // Measures the time of an action. Lambda expressions are used to pass the action.
        public static double MeasureExecutionTime(Action action) {
            Stopwatch stopwatch = new Stopwatch();
            stopwatch.Start();
            action();
            stopwatch.Stop();
            return stopwatch.Elapsed.TotalMilliseconds;
        }

        public (string depthLogFile, string timeLogFile) InitializeLogs(bool logVolumeData, bool logTimeData) {
            string depthLogFile = path + "VolumeData-" + transform.name + ".csv";
            string timeLogFile = path + "TimeData-" + transform.name + ".csv";

            if (!File.Exists(depthLogFile) && logVolumeData) {
                print("Beginning to log volume data");
                LogDataToFile(depthLogFile, "depth", "volume");
                // Add a constant downward force
                GetComponent<Rigidbody>().linearVelocity = new Vector3(0f, -0.1f, 0f);
            }

            if (!File.Exists(timeLogFile) && logTimeData) {
                print("Beginning to log time data");
                LogDataToFile(timeLogFile, "iteration_number", "time");
            }

            return (depthLogFile, timeLogFile);
        }
    }
}
