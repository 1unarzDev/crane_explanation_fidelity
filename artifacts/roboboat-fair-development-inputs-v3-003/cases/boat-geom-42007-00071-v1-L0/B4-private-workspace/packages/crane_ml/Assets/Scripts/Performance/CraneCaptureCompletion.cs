using System;
using System.IO;
using System.Text.RegularExpressions;

namespace Sim.Performance {
    // Opt-in benchmark termination only. The launcher publishes this marker
    // atomically after fixture process exit and complete capture validation.
    public sealed class CraneCaptureCompletion {
        public const string MarkerOption = "--crane-capture-complete-marker";
        public const string TokenOption = "--crane-capture-complete-token";
        public const double ShutdownDrainSeconds = 2;
        private readonly string path;
        private readonly string token;
        private double? observedAt;

        private CraneCaptureCompletion(string path, string token) {
            this.path = path;
            this.token = token;
            if (!Path.IsPathRooted(path)) throw new ArgumentException("Absolute completion path required");
            if (!Regex.IsMatch(token, "\\A[a-f0-9]{64}\\z"))
                throw new ArgumentException("64 lowercase hex completion token required");
            if (File.Exists(path) || Directory.Exists(path))
                throw new ArgumentException("Completion destination must be fresh");
        }

        public static CraneCaptureCompletion Parse(string[] args) {
            string marker = ReadUnique(args, MarkerOption);
            string token = ReadUnique(args, TokenOption);
            if (marker == null && token == null) return null;
            if (marker == null || token == null) throw new ArgumentException("Both completion options required");
            return new CraneCaptureCompletion(marker, token);
        }

        private static string ReadUnique(string[] args, string option) {
            string found = null;
            for (int i = 0; i < args.Length; i++) {
                if (args[i] != option) continue;
                if (found != null || i + 1 >= args.Length || string.IsNullOrEmpty(args[i + 1]))
                    throw new ArgumentException("Missing or duplicate completion option: " + option);
                found = args[++i];
            }
            return found;
        }

        public bool Ready(double wallSeconds) {
            if (double.IsNaN(wallSeconds) || double.IsInfinity(wallSeconds) || wallSeconds < 0)
                throw new ArgumentException("Finite nonnegative elapsed time required");
            if (!observedAt.HasValue && File.Exists(path)) {
                if (File.ReadAllText(path) != token + "\n")
                    throw new InvalidDataException("Capture completion token mismatch");
                observedAt = wallSeconds;
            }
            return observedAt.HasValue && wallSeconds - observedAt.Value >= ShutdownDrainSeconds;
        }
    }
}
