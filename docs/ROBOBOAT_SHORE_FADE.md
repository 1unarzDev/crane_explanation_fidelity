# RoboBoat underwater sand fade

The visible rectangular cutoff in the recording demo is the north edge of the
`Shore` Terrain, at Unity world z = -5.5. The original terrain is 120 × 50 meters,
starts at (-53.71, -0.8, -55.5), and uses the sand02 material. It ends abruptly
under shallow water, so the underwater surface remains visible right up to its
rectangular boundary.

`Assets/Editor/CraneShoreVisualInspection.cs` inspects this scene and applies a
reversible visual correction through Unity Editor APIs. Its `ApplyDepthFade`
method creates `Assets/Terrain/ShoreVisualFade.asset` and the child terrain
`Shore/Shore Fade Visual`. Within 14 meters of the perimeter, underwater sand
descends smoothly to 20 meters below its original level. The water's depth
attenuation softens the transition. Terrain above -0.15 meters is preserved;
the underwater transition reaches full strength below -0.65 meters. Interior
terrain farther than 14 meters from an edge retains its original height.

The original `Shore` Terrain renderer has `drawHeightmap=false`. Its
`TerrainCollider` still references the original, unmodified `Shore.asset`.
The visual child has no Collider. Nav2, LiDAR geometry, and collision geometry
therefore retain their original terrain. Restore the original presentation by
enabling `Shore.drawHeightmap` and disabling/removing `Shore Fade Visual`.

Verification artifacts are in
`artifacts/nav2-docking-reproduction-20261002/`:

- `shore-inspection.json`: actual scene terrain and dock Renderer/Collider bounds.
- `shore-fade-apply.log`: successful Unity Editor invocation with
  `CRANE_SHORE_FADE_COMPLETE`; no C# compilation errors.
- `shore-fade-verification.json`: the original collider TerrainData exactly
  matches Git HEAD, SHA256
  `23254db40dc30e869bc63c9add0f63963673bc3e8d17342b989972e7ef92dee2`.

Fresh player visual verification passed. `build-shore-first-dock.log` records
`CRANE_BUILD_COMPLETE` for `Builds/CRANE-Evidence-ShoreFade/CRANE.x86_64` and
explicitly includes `ShoreVisualFade.asset`. Pixel inspection of
`first-dock-shore/first-dock.png` shows the former rectangular foreground edge
has disappeared and the sand transitions gradually into deeper water. The
image hash and verification result are retained in `shore-fade-verification.json`.

The scene-derived first dock is `Marina/Dock0`, Unity world x =
[15.8357, 18.8380], z = [-0.8861, 6.6142]. The second dock is `Marina/Dock1`,
x = [23.3369, 26.3369], z = [-0.8859, 6.6141]. Dock0's slip entrances are along
its east edge at x ≈ 18.837, with clear gaps z = [0.114, 1.614],
[2.114, 3.614], and [4.114, 5.614]. These bounds identify the first dock for
capture timing independently of screenshot interpretation.
