using System;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.IO;
using System.Threading;
using UnityEngine;

namespace Sim.Utils.Performance {
    [Serializable] public sealed class CraneActionTimingEvent {
        public string kind, source, reason, policy, payloadEncoding;
        public byte[] payload;
        public long ordinal, monotonic, episode, sequence, sourceTick, receiveTick,
            applicationTick, decisionEpisode, maximumLagTicks, mailbox, rawSeconds, rawNanoseconds;
        public long callbackCompletionTick = -1, snapshotTick = -1;
        public long acceptedActions = -1, rejectedActions = -1, staleActions = -1,
            crossEpisodeActions = -1, duplicateActions = -1, unknownSourceActions = -1;
        public bool hadPending;
    }

    // All producer paths buffer only. Serialization and IO run in the owner drain.
    // A closed session rejects late callbacks; StopRecording unsubscribes before final drain.
    public static class CraneActionTimingAudit {
        public const int DefaultCapacity = 100000;
        public const int DefaultMaximumPayloadBytes = 65536;
        public const int DefaultPayloadByteCapacity = 16777216;
        private sealed class Buffer {
            public readonly object sync = new();
            public readonly ConcurrentQueue<CraneActionTimingEvent> queue = new();
            public readonly int capacity, maximumPayloadBytes, payloadByteCapacity;
            public int count, payloadBytes, failed, closed, subscribed;
            public long dropped, ordinal, written, enqueued, attempts;
            public Action<CraneAcceptedAction> observer;
            public Buffer(int capacity, int maximumPayloadBytes, int payloadByteCapacity) {
                this.capacity = capacity; this.maximumPayloadBytes = maximumPayloadBytes;
                this.payloadByteCapacity = payloadByteCapacity;
            }
        }
        private static readonly object lifecycle = new();
        private static Buffer active;
        private static long mailboxSequence;
        public static long NewMailbox() => Interlocked.Increment(ref mailboxSequence);
        public static bool Enabled => Volatile.Read(ref active) is Buffer b && Volatile.Read(ref b.closed) == 0;
        public static long Dropped => Volatile.Read(ref active) is Buffer b ? Interlocked.Read(ref b.dropped) : 0;
        public static int Buffered => Volatile.Read(ref active) is Buffer b ? Volatile.Read(ref b.count) : 0;
        public static int BufferedPayloadBytes => Volatile.Read(ref active) is Buffer b ? Volatile.Read(ref b.payloadBytes) : 0;
        public static long Written => Volatile.Read(ref active) is Buffer b ? Interlocked.Read(ref b.written) : 0;
        public static long Enqueued => Volatile.Read(ref active) is Buffer b ? Interlocked.Read(ref b.enqueued) : 0;
        public static long EventAttempts => Volatile.Read(ref active) is Buffer b ? Interlocked.Read(ref b.attempts) : 0;
        public static bool WriterFailed => Volatile.Read(ref active) is Buffer b && Volatile.Read(ref b.failed) != 0;
        public static bool AcceptedObserverSubscribed => Volatile.Read(ref active) is Buffer b && Volatile.Read(ref b.subscribed) != 0;
        public static void StartBuffer(int capacity = DefaultCapacity,
            int maximumPayloadBytes = DefaultMaximumPayloadBytes,
            int payloadByteCapacity = DefaultPayloadByteCapacity) {
            if (capacity < 1 || maximumPayloadBytes < 0 || payloadByteCapacity < 0)
                throw new ArgumentOutOfRangeException(nameof(capacity));
            lock (lifecycle) {
                if (active != null) throw new InvalidOperationException("End and drain the existing audit session before replacing it");
                var b = new Buffer(capacity, maximumPayloadBytes, payloadByteCapacity);
                b.observer = action => RecordAccepted(b, action);
                Volatile.Write(ref active, b);
                CraneActionGate.SubscribeAcceptedActions(b.observer);
                Volatile.Write(ref b.subscribed, 1);
            }
        }
        public static void StopRecording() {
            lock (lifecycle) {
                Buffer b = Volatile.Read(ref active);
                if (b == null) return;
                // No gate lock is held while acquiring the buffer lock or vice versa.
                lock (b.sync) b.closed = 1;
                if (Interlocked.Exchange(ref b.subscribed, 0) != 0)
                    CraneActionGate.UnsubscribeAcceptedActions(b.observer);
            }
        }
        public static void Disable() {
            lock (lifecycle) {
                StopRecording();
                Volatile.Write(ref active, null);
            }
        }
        public static void Record(string kind, in CraneActionReceipt receipt, long mailbox = 0,
            string reason = "", bool hadPending = false, long applicationTick = -1,
            CraneActionPolicy policy = CraneActionPolicy.LatestValid, long maximumLagTicks = -1,
            long decisionEpisode = -1, long rawSeconds = 0, long rawNanoseconds = 0) {
            Buffer b = Volatile.Read(ref active);
            if (b == null || Volatile.Read(ref b.closed) != 0) return;
            RecordTo(b, kind, receipt, mailbox, reason, hadPending, applicationTick, policy,
                maximumLagTicks, decisionEpisode, rawSeconds, rawNanoseconds);
        }
        private static void RecordAccepted(Buffer b, CraneAcceptedAction action) {
            // Delegate snapshots may outlive unsubscribe. The closed-session guard in RecordTo
            // prevents an old delegate from writing into a subsequent session.
            if (!ReferenceEquals(Volatile.Read(ref active), b)) return;
            try {
                long completionTick = CraneRuntimeMetrics.SimulationTick;
                var receipt = new CraneActionReceipt(action.Source, action.EpisodeId,
                    action.Sequence, action.SourceObservationTick, action.ReceiveTick);
                RecordTo(b, "post_apply_callback", receipt, applicationTick: action.ApplicationTick,
                    callbackCompletionTick: completionTick, payloadEncoding: action.Payload.Encoding,
                    payload: action.Payload.Data);
            } catch {
                lock (b.sync) { if (b.closed == 0) { b.attempts++; b.dropped++; } }
            }
        }
        private static void RecordTo(Buffer b, string kind, in CraneActionReceipt receipt,
            long mailbox = 0, string reason = "", bool hadPending = false,
            long applicationTick = -1, CraneActionPolicy policy = CraneActionPolicy.LatestValid,
            long maximumLagTicks = -1, long decisionEpisode = -1, long rawSeconds = 0,
            long rawNanoseconds = 0, long callbackCompletionTick = -1,
            string payloadEncoding = null, byte[] payload = null,
            long snapshotTick = -1, long acceptedActions = -1, long rejectedActions = -1,
            long staleActions = -1, long crossEpisodeActions = -1,
            long duplicateActions = -1, long unknownSourceActions = -1) {
            lock (b.sync) {
                if (b.closed != 0) return;
                b.attempts++;
                int bytes = payload?.Length ?? 0;
                if (b.failed != 0 || b.count >= b.capacity || bytes > b.maximumPayloadBytes ||
                    bytes > b.payloadByteCapacity - b.payloadBytes) { b.dropped++; return; }
                try {
                    byte[] ownedPayload = payload == null ? null : (byte[])payload.Clone();
                    var value = new CraneActionTimingEvent {
                        kind = kind, source = receipt.Source, reason = reason, hadPending = hadPending,
                        ordinal = b.ordinal + 1, monotonic = Stopwatch.GetTimestamp(),
                        episode = receipt.EpisodeId, sequence = receipt.Sequence,
                        sourceTick = receipt.SourceObservationTick, receiveTick = receipt.ReceiveTick,
                        applicationTick = applicationTick, decisionEpisode = decisionEpisode,
                        policy = maximumLagTicks >= 0 ? policy.ToString() : "not_captured",
                        maximumLagTicks = maximumLagTicks, mailbox = mailbox,
                        rawSeconds = rawSeconds, rawNanoseconds = rawNanoseconds,
                        callbackCompletionTick = callbackCompletionTick,
                        payloadEncoding = payloadEncoding, payload = ownedPayload,
                        snapshotTick = snapshotTick, acceptedActions = acceptedActions,
                        rejectedActions = rejectedActions, staleActions = staleActions,
                        crossEpisodeActions = crossEpisodeActions, duplicateActions = duplicateActions,
                        unknownSourceActions = unknownSourceActions
                    };
                    b.queue.Enqueue(value); b.ordinal++; b.count++;
                    b.payloadBytes += bytes; b.enqueued++;
                } catch { b.dropped++; }
            }
        }
        public static bool TryRead(out CraneActionTimingEvent value) {
            Buffer b = Volatile.Read(ref active);
            if (b != null) {
                lock (b.sync) {
                    if (b.queue.TryDequeue(out value)) {
                        b.count--; b.payloadBytes -= value.payload?.Length ?? 0; return true;
                    }
                }
            }
            value = null; return false;
        }
        public static void Drain(TextWriter writer) {
            Buffer b = Volatile.Read(ref active);
            if (b == null || Volatile.Read(ref b.failed) != 0) return;
            try {
                while (TryRead(out CraneActionTimingEvent value)) {
                    try { writer.WriteLine(JsonUtility.ToJson(value)); }
                    catch { lock (b.sync) b.dropped++; throw; }
                    lock (b.sync) b.written++;
                }
                writer.Flush();
            } catch {
                lock (b.sync) {
                    b.failed = 1;
                    while (b.queue.TryDequeue(out var pending)) {
                        b.count--; b.payloadBytes -= pending.payload?.Length ?? 0; b.dropped++;
                    }
                }
            }
        }
        public static void RecordRosCallback(string source, long sequence, long sourceTick,
            long seconds, long nanoseconds) {
            if (!Enabled) return;
            var receipt = new CraneActionReceipt(source, CraneRuntimeMetrics.EpisodeId, sequence,
                sourceTick, CraneRuntimeMetrics.SimulationTick);
            Record("ros_callback", receipt, rawSeconds: seconds, rawNanoseconds: nanoseconds);
        }
        public static void RecordCounterSnapshot(long episode, long snapshotTick,
            long acceptedActions, long rejectedActions, long staleActions,
            long crossEpisodeActions, long duplicateActions, long unknownSourceActions) {
            Buffer b = Volatile.Read(ref active);
            if (b == null || Volatile.Read(ref b.closed) != 0) return;
            var receipt = new CraneActionReceipt("worker", episode, -1, -1, snapshotTick);
            RecordTo(b, "counter_snapshot", receipt, reason: "worker_action_timing_snapshot",
                snapshotTick: snapshotTick, acceptedActions: acceptedActions,
                rejectedActions: rejectedActions, staleActions: staleActions,
                crossEpisodeActions: crossEpisodeActions, duplicateActions: duplicateActions,
                unknownSourceActions: unknownSourceActions);
        }
        public static void MarkWriterFailed() {
            Buffer b = Volatile.Read(ref active);
            if (b != null) lock (b.sync) b.failed = 1;
        }
    }

    public sealed class CraneActionTimingAuditWriter : MonoBehaviour {
        private StreamWriter writer;
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void Initialize() {
            string[] args = Environment.GetCommandLineArgs();
            int index = Array.IndexOf(args, "--crane-action-timing-audit");
            if (index < 0) return;
            CraneActionTimingAudit.StartBuffer();
            var owner = new GameObject("CraneActionTimingAudit");
            DontDestroyOnLoad(owner);
            var component = owner.AddComponent<CraneActionTimingAuditWriter>();
            try {
                if (index + 1 >= args.Length) throw new ArgumentException("Missing audit path");
                component.writer = new StreamWriter(args[index + 1], false);
                component.writer.WriteLine("{\"kind\":\"metadata\",\"schema\":\"action-timing-v9\",\"clock\":\"same-process-stopwatch\",\"frequency\":" + Stopwatch.Frequency + ",\"capacity\":100000,\"maxPayloadBytes\":65536,\"payloadByteCapacity\":16777216,\"acceptedObserverSubscribed\":true}");
                component.writer.Flush();
            } catch { CraneActionTimingAudit.MarkWriterFailed(); }
        }
        private void LateUpdate() { if (writer != null) CraneActionTimingAudit.Drain(writer); }
        private void OnDestroy() {
            CraneActionTimingAudit.StopRecording();
            if (writer == null) return;
            CraneActionTimingAudit.Drain(writer);
            try {
                writer.WriteLine("{\"kind\":\"footer\",\"dropped\":" + CraneActionTimingAudit.Dropped +
                    ",\"buffered\":" + CraneActionTimingAudit.Buffered +
                    ",\"bufferedPayloadBytes\":" + CraneActionTimingAudit.BufferedPayloadBytes +
                    ",\"written\":" + CraneActionTimingAudit.Written +
                    ",\"enqueued\":" + CraneActionTimingAudit.Enqueued +
                    ",\"eventAttempts\":" + CraneActionTimingAudit.EventAttempts +
                    ",\"acceptedObserverSubscribed\":" + (CraneActionTimingAudit.AcceptedObserverSubscribed ? "true" : "false") +
                    ",\"writerFailed\":" + (CraneActionTimingAudit.WriterFailed ? "true" : "false") + "}");
                writer.Dispose();
            } catch { CraneActionTimingAudit.MarkWriterFailed(); }
        }
    }
}
