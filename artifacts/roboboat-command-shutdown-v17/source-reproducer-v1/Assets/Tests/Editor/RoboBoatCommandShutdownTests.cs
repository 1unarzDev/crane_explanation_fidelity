using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using NUnit.Framework;
using RosMessageTypes.Geometry;
using Sim.Controllers;
using Sim.Utils.Performance;
using UnityEngine;

public sealed class RoboBoatCommandShutdownTests {
    private GameObject owner;
    private ROSOmniXCommand adapter;
    [SetUp] public void Setup() {
        CraneActionTimingAudit.Disable(); CraneRuntimeMetrics.BeginEpisode();
        CraneActionTimingAudit.StartBuffer();
        owner = new GameObject("shutdown-command-test");
        adapter = owner.AddComponent<ROSOmniXCommand>();
        typeof(ROSOmniXCommand).GetField("topic", BindingFlags.NonPublic | BindingFlags.Instance)
            .SetValue(adapter, "/crane/cmd_vel_stamped");
    }
    [TearDown] public void Cleanup() {
        if (owner != null) Object.DestroyImmediate(owner);
        CraneActionTimingAudit.Disable();
    }
    private void Receive() {
        typeof(ROSOmniXCommand).GetMethod("Receive", BindingFlags.NonPublic | BindingFlags.Instance)
            .Invoke(adapter, new object[] { new TwistStampedMsg() });
    }
    private static List<CraneActionTimingEvent> Events() {
        var events = new List<CraneActionTimingEvent>();
        while (CraneActionTimingAudit.TryRead(out var item)) events.Add(item);
        return events;
    }
    [Test] public void DisablingRealAdapterDisposesItsPendingReceipt() {
        Receive(); adapter.enabled = false;
        var events = Events();
        Assert.That(events.Count(e => e.kind == "mailbox_enqueue"), Is.EqualTo(1));
        var enqueue = events.Single(e => e.kind == "mailbox_enqueue");
        Assert.That(events.Any(e => e.kind == "mailbox_clear" && e.hadPending
            && e.mailbox == enqueue.mailbox && e.sequence == enqueue.sequence), Is.True,
            "Actual adapter left a receipt pending when disabled before the next physics step");
    }
    [Test] public void CallbackAfterDisableCannotReopenMailbox() {
        adapter.enabled = false; Receive();
        Assert.That(Events().Any(e => e.kind == "mailbox_enqueue"), Is.False,
            "Transport callback reopened disabled adapter mailbox");
    }
    [Test] public void DestroyingRealAdapterDisposesItsPendingReceiptBeforeAuditClosure() {
        Receive(); Object.DestroyImmediate(owner); owner = null;
        Assert.That(Events().Any(e => e.kind == "mailbox_clear" && e.hadPending), Is.True);
    }
}
