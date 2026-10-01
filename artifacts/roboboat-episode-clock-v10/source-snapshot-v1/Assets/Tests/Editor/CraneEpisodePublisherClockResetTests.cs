using System;
using System.Reflection;
using NUnit.Framework;
using Sim.Controllers;
using Sim.Utils.Performance;
using Sim.Utils.ROS;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine;

public sealed class CraneEpisodePublisherClockResetTests {
    private GameObject owner;
    private ROSConnection connection;

    [SetUp] public void SetUp() {
        CraneRuntimeMetrics.BeginEpisode();
        owner = new GameObject("epoch-publisher-test");
        connection = ROSConnection.GetOrCreateInstance();
    }
    [TearDown] public void TearDown() {
        if (owner != null) UnityEngine.Object.DestroyImmediate(owner);
        if (connection != null) UnityEngine.Object.DestroyImmediate(connection.gameObject);
        CraneRuntimeMetrics.BeginEpisode();
    }
    private static void Set(object instance, string name, object value) =>
        instance.GetType().GetField(name, BindingFlags.Instance | BindingFlags.NonPublic).SetValue(instance, value);
    private static double Get(object instance, string name) =>
        (double)instance.GetType().GetField(name, BindingFlags.Instance | BindingFlags.NonPublic).GetValue(instance);
    private static void Invoke(object instance, string name) =>
        instance.GetType().GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic).Invoke(instance, null);

    [Test] public void NavigationPublisherContinuesAfterBenchmarkClockResetWithoutBodyReset() {
        var body = owner.AddComponent<Rigidbody>();
        var publisher = owner.AddComponent<CraneROSNavigationState>();
        publisher.Initialize(body, "/epoch-test/odom", "/epoch-test/tf", "odom", "base_link", 50f,
            Array.Empty<string>());
        // Retained failure: the warmup deadline is about2.9s, then measurement
        // calls BeginEpisode without resetting the physical body/components.
        Set(publisher, "nextPublishTime", 2.9d);
        CraneRuntimeMetrics.BeginEpisode();
        Invoke(publisher, "FixedUpdate");
        Assert.That(Get(publisher, "nextPublishTime"), Is.LessThan(0.03d),
            "Fresh episode must publish immediately; a warmup deadline must not suppress odometry.");
    }

    [Test] public void RosClockDoesNotRetainWarmupDeadlineAfterBenchmarkClockReset() {
        var publisher = owner.AddComponent<ROSClock>();
        Invoke(publisher, "Start");
        Set(publisher, "lastPublishTimeSeconds", 2.9d);
        CraneRuntimeMetrics.BeginEpisode();
        Invoke(publisher, "Update");
        Assert.That(Get(publisher, "lastPublishTimeSeconds"), Is.LessThan(0.03d),
            "Clock scheduling must reset even when no body-reset callback is dispatched.");
    }
    [Test] public void NavigationPublisherPreservesSameEpisodeDeadline() {
        var publisher = owner.AddComponent<CraneROSNavigationState>();
        publisher.Initialize(owner.AddComponent<Rigidbody>(), "/epoch-test/odom", "/epoch-test/tf",
            "odom", "base_link", 50f, Array.Empty<string>());
        Set(publisher, "nextPublishTime", 2.9d);
        Invoke(publisher, "FixedUpdate");
        Assert.That(Get(publisher, "nextPublishTime"), Is.EqualTo(2.9d));
    }

    [Test] public void RosClockPreservesSameEpisodeDeadline() {
        var publisher = owner.AddComponent<ROSClock>();
        Invoke(publisher, "Start");
        Set(publisher, "lastPublishTimeSeconds", 2.9d);
        Invoke(publisher, "Update");
        Assert.That(Get(publisher, "lastPublishTimeSeconds"), Is.EqualTo(2.9d));
    }

    [Test] public void NavigationPublisherPreservesExplicitBeforePhysicsReset() {
        var publisher = owner.AddComponent<CraneROSNavigationState>();
        publisher.Initialize(owner.AddComponent<Rigidbody>(), "/epoch-test/odom", "/epoch-test/tf",
            "odom", "base_link", 50f, Array.Empty<string>());
        Set(publisher, "nextPublishTime", 2.9d);
        publisher.ResetEpisode(default, CraneEpisodeResetPhase.BeforePhysics);
        Assert.That(Get(publisher, "nextPublishTime"), Is.EqualTo(0d));
    }

    [Test] public void RosClockPreservesExplicitBeforePhysicsReset() {
        var publisher = owner.AddComponent<ROSClock>();
        Invoke(publisher, "Start");
        Set(publisher, "lastPublishTimeSeconds", 2.9d);
        publisher.ResetEpisode(default, CraneEpisodeResetPhase.BeforePhysics);
        Assert.That(Get(publisher, "lastPublishTimeSeconds"), Is.LessThan(0d));
    }

}
