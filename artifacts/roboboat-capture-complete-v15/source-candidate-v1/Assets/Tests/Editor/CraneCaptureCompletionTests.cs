using System;
using System.IO;
using NUnit.Framework;
using Sim.Performance;

public sealed class CraneCaptureCompletionTests {
    private string folder;
    private string marker;
    private const string Token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    [SetUp] public void Setup() {
        folder = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(folder); marker = Path.Combine(folder, "complete");
    }
    [TearDown] public void Cleanup() { Directory.Delete(folder, true); }
    private CraneCaptureCompletion Gate() => CraneCaptureCompletion.Parse(new[] {
        CraneCaptureCompletion.MarkerOption, marker, CraneCaptureCompletion.TokenOption, Token });

    [Test] public void DisabledWithoutOptions() {
        Assert.That(CraneCaptureCompletion.Parse(new[] { "worker" }), Is.Null);
    }
    [Test] public void MarkerRequiresExactTokenAndFullDrain() {
        var gate = Gate(); Assert.That(gate.Ready(100), Is.False);
        string temporary = marker + ".tmp"; File.WriteAllText(temporary, Token + "\n");
        Assert.That(gate.Ready(101), Is.False); File.Move(temporary, marker);
        Assert.That(gate.Ready(102), Is.False);
        Assert.That(gate.Ready(103.999), Is.False);
        Assert.That(gate.Ready(104), Is.True);
    }
    [Test] public void PreexistingMarkerRejected() {
        File.WriteAllText(marker, Token + "\n"); Assert.Throws<ArgumentException>(() => Gate());
    }
    [Test] public void WrongOrPartialTokenCannotFinish() {
        var gate = Gate(); File.WriteAllText(marker, "partial");
        Assert.Throws<InvalidDataException>(() => gate.Ready(100));
    }
    [Test] public void MissingDuplicateRelativeAndMalformedOptionsRejected() {
        Assert.Throws<ArgumentException>(() => CraneCaptureCompletion.Parse(new[] { CraneCaptureCompletion.MarkerOption }));
        Assert.Throws<ArgumentException>(() => CraneCaptureCompletion.Parse(new[] { CraneCaptureCompletion.TokenOption, Token }));
        Assert.Throws<ArgumentException>(() => CraneCaptureCompletion.Parse(new[] {
            CraneCaptureCompletion.MarkerOption, "relative", CraneCaptureCompletion.TokenOption, Token }));
        Assert.Throws<ArgumentException>(() => CraneCaptureCompletion.Parse(new[] {
            CraneCaptureCompletion.MarkerOption, marker, CraneCaptureCompletion.TokenOption, "NaN" }));
        Assert.Throws<ArgumentException>(() => CraneCaptureCompletion.Parse(new[] {
            CraneCaptureCompletion.MarkerOption, marker, CraneCaptureCompletion.TokenOption, Token,
            CraneCaptureCompletion.TokenOption, Token }));
    }
    [Test] public void NonfiniteTimeRejected() {
        var gate = Gate(); Assert.Throws<ArgumentException>(() => gate.Ready(double.NaN));
        Assert.Throws<ArgumentException>(() => gate.Ready(double.PositiveInfinity));
    }
}
