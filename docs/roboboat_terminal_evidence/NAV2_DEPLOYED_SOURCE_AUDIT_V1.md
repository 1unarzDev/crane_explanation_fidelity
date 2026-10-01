# Deployed Nav2 source and binary audit v1

The audit now binds public Nav2 implementation to the **actual observed episode container**, rather than inferring deployment from an image tag. It substantially closes the version/source gap but does not establish exact Debian source-package authenticity or source-to-binary build equivalence. No architecture baseline or call readiness is promoted.

## Observed deployment

The root observation at `artifacts/roboboat-deployed-nav2-audit-v1-001/observation.json` records the controller container used by development geometry `42004-00002-v1`, its episode container-ID receipt, image ID `sha256:9c286b78dcc1ecf0a159f624f642cf831d463370ce264f00fdd6f6c30ce50053`, package identities and 57 preserved installed public headers, binaries and metadata files. The four packages are:

| Installed package | Exact installed binary version |
|---|---|
| ros-jazzy-nav2-core | 1.3.12-1noble.20260615.164834 |
| ros-jazzy-nav2-bt-navigator | 1.3.12-1noble.20260615.165211 |
| ros-jazzy-nav2-controller | 1.3.12-1noble.20260615.165600 |
| ros-jazzy-nav2-regulated-pure-pursuit-controller | 1.3.12-1noble.20260615.170110 |

The `.20260615.*` suffix is an installed **binary build version**, not proof of an identically named Debian source version. Public release/debian source tags identify `1.3.12-1` / `1.3.12-1noble`.

Initial read-only `apt-cache show` inspection found the exact installed controller metadata; `apt-cache showsrc` could not operate because the active container has no deb-src URIs. No apt configuration was changed. The episode container ended normally before a later attempted key copy, so that copy failed with “No such container.” No container was killed, restarted or changed, and no new image/platform was installed.

## Matching commit-bound public source

`analysis/audit_roboboat_nav2_source_v1.py` validates every preserved installed-file hash and episode receipt before fetching matching ROS release and Noble Debian tags from `ros2-gbp/navigation2-release`. GitHub API refs and codeload source archives use certificate-verified HTTPS. Eight exact commits, original responses, downloaded archives and extracted source hashes are retained in `artifacts/roboboat-nav2-release-source-audit-v1-001/source-audit.json` and its source tree.

For each of controller, core, regulated pure pursuit and BT navigator, the audit preserves both `release/jazzy/{package}/1.3.12-1` and `debian/ros-jazzy-{package}_1.3.12-1_noble`. The generated controller Debian changelog records `1.3.12-1noble`; the matching Git release is a precise public implementation candidate, not a guessed generic Jazzy source branch. The current rosdistro distribution has already advanced to 1.3.13, so its current version was not substituted for the deployed package.

**All 45 preserved installed public headers and source-distributed metadata files are byte-identical to the package release source. There are zero mismatches and zero unmapped source files.** This includes stopped/simple goal-checker headers and controller, core, RPP and BT navigator interfaces. The separate `release-debian-comparison.json` shows all 89 nonpackaging release files across the four packages also match their generated Debian Git source trees. Exact implementation `.cpp` files, CMake/package metadata and public headers are now locally preserved for source inspection.

This is matching public source supported by exact installed-header/metadata equality. It does not independently prove that a particular `.cpp` file, build flag or dependency produced an installed shared library.

## Exact binary-package payload comparison

The June 18 Jazzy archive remains available at `http://snapshots.ros.org/jazzy/2026-06-18/ubuntu/`; it retains the exact four observed amd64 binary package versions. `analysis/audit_roboboat_nav2_binary_packages_v1.py` downloads those versions, checks retained package-index SHA256/size, safely reads their Debian ar/tar payloads and compares every observed installed file. Original Packages.gz, InRelease, four debs and `binary-package-audit.json` are retained in `artifacts/roboboat-nav2-binary-package-audit-v1-001`.

**All 57 observed installed files, including controller/goal-checker/RPP/BT binaries, are byte-identical to those exact binary-package payloads. There are zero mismatches and zero missing payloads.** This is a direct byte comparison to the actual preserved episode files, so it does not rely solely on dpkg version strings or current image tags.

Cryptographic repository authenticity remains qualified. HTTPS for packages.ros.org and snapshots.ros.org failed hostname validation; certificate checks were not bypassed. The package-index/archive retrieval used HTTP and checks the retained published index hashes, without claiming that unsigned transport authenticates their origin. The retained InRelease names signer `4B63CF8FDE49746E98FA01DDAD19BAB3CBF125EA`. `gpgv` could not verify it with either certificate-verified current ROS `ros.key` or `ros.asc`; it returned NO_PUBKEY. Keys, exact verification inputs, stdout/stderr and failure are preserved in `signature-verification.json`. Downloaded current keys are not presented as the actual episode's trusted keys.

The current ROS source index contains 1.3.13 source archives. Guessed exact 1.3.12 `.dsc` paths in current main/testing pools returned 404. The June archive's `main` index has binary architecture indices and no source index, while its controller pool lists matching deb/dbgsym archives. Thus exact original `.dsc`, `.orig.tar.gz`, Debian archive, signed source-index and build-farm `.buildinfo` provenance were not retrieved or authenticated. No source package was fabricated from matching Git to disguise that gap.

## Interpretation and next move

There are now three distinct positive observations: episode-bound installed byte snapshots; matching immutable release/debian Git source with 45 exact source-file matches; and exact binary deb payload equality for all 57 installed files. Remaining claims are explicitly absent: authenticated exact Debian source archive, verified apt signing chain, reproduced compiler/dependency build, and installed binary/source build equivalence.

The next feasible move is to retrieve the archive signer from an authoritative historical ROS key source or a separately episode/image-bound trusted keyring; verify InRelease, its Packages.gz digest and all four deb hashes; and request retained build-farm source artifacts or `.buildinfo` for these exact build timestamps. A deterministic source rebuild would require the matching toolchain and dependency lock and is a separate task. Meanwhile the matching public implementation can be offered symmetrically as **version-matched source with disclosed build-provenance limits**, if a later scientific interface decision accepts that bounded interpretation; it must not be labeled authenticated deployed source without resolving the remaining gap. Actual sandbox/scratch capability and Unity common-source/active-profile wiring still need their separate checks.

No provider calls, study answer or annotation reads, capture changes, active-worker mutations, source-freeze changes, primary promotion or historical image inference occurred. Both additive tools operate on public package metadata/source and preserved installation bytes. Ten focused parsing/admission tests pass; source retrieval tests use construction archives and mock network responses. Test results establish tooling behavior, not semantic study outcomes.
