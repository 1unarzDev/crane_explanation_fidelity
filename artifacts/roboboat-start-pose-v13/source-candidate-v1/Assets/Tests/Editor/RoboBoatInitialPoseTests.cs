using System;
using System.Globalization;
using NUnit.Framework;
using Sim.Controllers;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public sealed class RoboBoatInitialPoseTests {
    [Test] public void NoOverrideLeavesDefaultUntouched() {
        Assert.That(RoboBoatInitialPose.TryParse(new[] { "--crane-worker" }, out _), Is.False);
    }

    [Test] public void NegativeValuesUseInvariantCulture() {
        CultureInfo previous = CultureInfo.CurrentCulture;
        try {
            CultureInfo.CurrentCulture = new CultureInfo("de-DE");
            Assert.That(RoboBoatInitialPose.TryParse(new[] {
                RoboBoatInitialPose.Option, "-2.25,-5.5,-1.25" }, out Vector3 pose), Is.True);
            Assert.That(pose, Is.EqualTo(new Vector3(-2.25f, -5.5f, -1.25f)));
        }
        finally { CultureInfo.CurrentCulture = previous; }
    }

    [TestCase("NaN,0,0")]
    [TestCase("0,Infinity,0")]
    [TestCase("0,0,-Infinity")]
    [TestCase("0,0")]
    [TestCase("1,2,3,4")]
    [TestCase("1,bad,3")]
    public void InvalidInputIsRejected(string value) {
        Assert.Throws<ArgumentException>(() => RoboBoatInitialPose.TryParse(
            new[] { RoboBoatInitialPose.Option, value }, out _));
    }

    [Test] public void MissingOrDuplicateOverrideIsRejected() {
        Assert.Throws<ArgumentException>(() => RoboBoatInitialPose.TryParse(
            new[] { RoboBoatInitialPose.Option }, out _));
        Assert.Throws<ArgumentException>(() => RoboBoatInitialPose.TryParse(new[] {
            RoboBoatInitialPose.Option, "1,2,3", RoboBoatInitialPose.Option, "4,5,6" }, out _));
    }

    [TestCase(0f)] [TestCase(1.5707963f)] [TestCase(-1.25f)]
    public void RequestedYawMatchesAuthoritativePublisherForward(float yaw) {
        Vector3 forward = RoboBoatRosFrame.Rotation(RoboBoatInitialPose.Rotation(yaw)) * Vector3.forward;
        var ros = CraneROSNavigationState.ToRosVector(forward);
        Assert.That(ros.x, Is.EqualTo(Math.Cos(yaw)).Within(1e-5));
        Assert.That(ros.y, Is.EqualTo(Math.Sin(yaw)).Within(1e-5));
    }

    [Test] public void PositionRoundTripsToRosAndKeepsSceneHeight() {
        var ros = CraneROSNavigationState.ToRosPoint(
            RoboBoatInitialPose.Position(new Vector3(-2.25f, -5.5f, 1f), 0.73f));
        Assert.That(ros.x, Is.EqualTo(-2.25f)); Assert.That(ros.y, Is.EqualTo(-5.5f));
        Assert.That(ros.z, Is.EqualTo(0.73f).Within(1e-6));
    }

    [Test] public void RigidbodyOverrideResetsMomentumAndPreservesHeight() {
        var owner = new GameObject("pose-test");
        try {
            owner.transform.position = new Vector3(10f, .73f, 20f);
            var body = owner.AddComponent<Rigidbody>(); body.useGravity = false;
            body.linearVelocity = Vector3.one; body.angularVelocity = Vector3.one;
            RoboBoatInitialPose.Apply(body, new Vector3(-2.25f, -5.5f, 0f));
            Assert.That(body.position, Is.EqualTo(new Vector3(5.5f, .73f, -2.25f)));
            Assert.That(body.linearVelocity, Is.EqualTo(Vector3.zero));
            Assert.That(body.angularVelocity, Is.EqualTo(Vector3.zero));
        }
        finally { UnityEngine.Object.DestroyImmediate(owner); }
    }

    [Test] public void ActualCourseUsesRootArticulationAndTeleportsWholeBoat() {
        Scene scene = EditorSceneManager.OpenScene("Assets/Scenes/Roboboat Course.unity", OpenSceneMode.Single);
        Component selected = RoboBoatInitialPose.FindBody(scene);
        Assert.That(selected, Is.InstanceOf<ArticulationBody>());
        var body = (ArticulationBody)selected; Assert.That(body.isRoot, Is.True);
        Vector3 initial = body.transform.position;
        try {
            RoboBoatInitialPose.Apply(body, new Vector3(-2.25f, -5.5f, -.3f));
            Assert.That(Vector3.Distance(body.transform.position, new Vector3(5.5f, initial.y, -2.25f)), Is.LessThan(1e-4f));
        }
        finally { EditorSceneManager.OpenScene("Assets/Scenes/Roboboat Course.unity", OpenSceneMode.Single); }
    }

    [Test] public void NonRoboBoatSceneCannotBeSelected() {
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        Assert.Throws<ArgumentException>(() => RoboBoatInitialPose.FindBody(scene));
    }
}
