# Fernández-Becerra robot-accountability and explanation precedents

**Audit date:** 2026-09-24
**Scope:** Primary-source check limited to the two works below and their author-released software.
This note positions the prospective CRANE physical-diagnosis study; it is not a reproduction, a
systematic review, or empirical evidence for CRANE.

## Bottom line

Fernández-Becerra et al.'s ESWA paper is close prior work for ROS 2/Nav2 accountability data,
event/source-aware retrieval, agentic RAG, retrieval and hallucination grading, calculations over
retrieved records, and natural-language explanations of navigation logs. The
IGPL paper is precedent for a replayable, privacy/authenticity-oriented black-box recorder and for
using textual robot logs together with visual/VLM context. CRANE should not claim novelty for any
of those capabilities.

The narrow distinction available to CRANE is an evaluation question, not a priority claim:
whether a system can **independently check a physical or execution mechanism** from retained
measurements and declared diagnostic computations, preserve provenance and conflicting evidence,
leave alternatives unresolved when the evidence is insufficient, and qualify or abstain—rather
than retrieve, repeat, or linguistically validate a causal statement already present in a log or
curated event. That claim must remain prospective until results from independent CRANE episode
clusters support it.

## ESWA 2026: verified precedent and limits

The published paper describes a ROS 2 Humble navigation system evaluated with an RB-1 robot in a
Gazebo hospital environment. Its recorder subscribes to Nav2 goal status, planned paths, `/rosout`,
AMCL pose, commanded velocity, and laser scans. It structures these messages with timestamps and
metadata and stores embeddings for retrieval ([paper, Sections 3.2 and 3.4](https://doi.org/10.1016/j.eswa.2026.132631),
[open author-repository copy](https://hdl.handle.net/10612/28306)). This establishes close prior art
for generating natural-language explanations from ROS/Nav2 runtime records.

The retrieval stack is stronger than a simple log-only prompt. It combines BM25 and vector search
with reciprocal-rank fusion, temporal metadata filtering, chronological reranking, iterative
retrieval, and six roles: Retriever, Retrieval Grader, Query Rewriter, Answer Generator,
Hallucination Grader, and Answer Grader. The hallucination grader checks whether each part of an
answer is traceable to retrieved data and conversation context and can trigger refinement
([paper, Sections 3.3.1–3.3.7](https://doi.org/10.1016/j.eswa.2026.132631)). The generator also
aggregates timestamps, calculates distances from recorded coordinates, and attributes messages to
ROS components ([paper, Section 3.3.5 and Figure 6](https://doi.org/10.1016/j.eswa.2026.132631)).
CRANE therefore must not present agentic RAG, hybrid/metadata-aware retrieval, source-aware log
explanations, calculations over retrieved records, or a hallucination grader as new. The paper
describes those calculations as model inferences; it does not document a separate deterministic
calculator tool.

“Source-aware” needs precise wording. The recorder preserves `/rosout` fields including node name,
message, file, function, and line, as the [released recorder
shows](https://github.com/laurafbec/RT_Accountability_Explainability/blob/main/rt_recorder_explainer/rt_recorder_explainer/kafka_producer_srv.py#L244-L261).
The audited paper and release do **not** establish a general repository/configuration-analysis
agent comparable to a baseline given the relevant repository and configuration files. CRANE may
still study exact runtime-to-source/configuration linkage, but not under the broad claim that
source-aware explanations are absent from prior work.

The most important evidence boundary appears inside the ESWA method itself. Its curation rule
detects a changed path and associates it with a nearby laser return using a predefined distance
threshold; it emits records such as “Path modified due to obstacle detection” or “Path modified
without obstacle detection” ([paper, Algorithm 1 and Section 3.2](https://doi.org/10.1016/j.eswa.2026.132631)).
The authors explicitly call these **local, limited, rule-based event attributions**, not complete
explanations. A downstream answer can thus be faithful to retrieved documents while repeating an
upstream attribution. The paper's hallucination grader verifies traceability to retrieved context;
it does not independently establish that an obstacle physically restricted the robot, entered the
costmap used by Nav2, caused the replanning decision, or explains a command-to-motion discrepancy.
This is the manuscript-safe point of differentiation for CRANE.

The ESWA evaluation used three navigation scenarios and sixteen questions spanning goal status,
replanning, topics, velocity, timing, positions/distances, logs, and responsible components. It
reports RAGAS/reference/LLM-judge metrics and an ablation in which each configuration was generated
five times per scenario (1,200 explanations total for the ablation)
([paper, Sections 4.1–4.5](https://doi.org/10.1016/j.eswa.2026.132631)). Repeated generations over
three underlying scenarios are not hundreds of independent robot episodes. CRANE should credit
this evaluation while keeping scenario-clustered inference and distinguishing independent episode
clusters from repeated LLM samples.

The authors release code, evaluation datasets, and instructions at
[`laurafbec/RT_Accountability_Explainability`](https://github.com/laurafbec/RT_Accountability_Explainability).
The release documents ROS 2 Humble, Kafka/Confluent, MongoDB Atlas Vector Search, LangGraph,
LangChain, RAGAS, external embedding/grading models, and the Agentic-RAG workflow. It is therefore
feasible to define a **small development-only compatibility check** at the structured-document
boundary: give the released explainer a fixed CRANE episode's same robot-visible records and ask a
small predeclared question set. This is optional, is not a reproduction study, and must not delay
independent CRANE episode collection or submission. A full deployment would add substantial
infrastructure and model/API matching. The GitHub repository is public but exposed no repository
license in the GitHub API at audit time, so reuse of code (rather than execution/inspection) also
requires a license check.

## IGPL: verified precedent and evidence boundary

The publisher's abstract describes a two-part proof of concept for ROS mobile robots: (1) a
black-box-like accountability module that captures robot actions while targeting faithful replay,
data privacy, and authenticity; and (2) a natural-language explanation component using LLMs and
VLMs to analyze textual logs with added visual context
([publisher record and abstract](https://doi.org/10.1093/jigpal/jzaf016)). This is direct precedent
for accountable recording and textual-plus-visual explanation context. CRANE should not claim
novelty for a robot black box, encrypted/authentic recording, multimodal/VLM context, or natural
language over those records.

The associated author release records ROS 2/Nav2 topics to rosbag, supports replay with `ros2 bag
play`, can trigger recording from a laser-distance threshold or a failed behavior-tree status, and
includes map, odometry, commands, scans, global/local costmaps, camera images, behavior-tree logs,
plans, and navigation status ([project README](https://github.com/laurafbec/nav2_accountability_explainability_vlms),
[recorder source at the original 2024 release](https://github.com/laurafbec/nav2_accountability_explainability_vlms/blob/0bcf784d12dac3570999d93eb24be411dc2b48f5/bag_recorder/bag_recorder/bag_recorder_srv.py)).
The release also contains AES-GCM message encryption with an RSA-OAEP-wrapped key and authentication
failure on altered ciphertext
([cipher](https://github.com/laurafbec/nav2_accountability_explainability_vlms/blob/6a9b8ac8d5624e9b43715deae8809bb60f79846a/bag_recorder/bag_recorder/bag_cipher_node.py),
[decipher/verification](https://github.com/laurafbec/nav2_accountability_explainability_vlms/blob/6a9b8ac8d5624e9b43715deae8809bb60f79846a/bag_recorder/bag_recorder/bag_decipher_node.py)).

The release's pinned explainer separates a text path that embeds and retrieves `/rosout` messages
from a visual path that asks a LLaVA ROS node to describe the center of a camera image
([text explainer](https://github.com/Dsobh/explainable_ROS/blob/68e171500d4c57f81f1e507795db6873a0533407/explicability_ros/explicability_ros/explicability_node.py),
[visual explainer](https://github.com/Dsobh/explainable_ROS/blob/68e171500d4c57f81f1e507795db6873a0533407/explicability_ros/explicability_ros/vexp_node.py)).
This supports the broad multimodal precedent, but it does not erase the evidence boundary:

> A camera image or VLM description showing an obstacle establishes only that the obstacle was
> visible in that image under the VLM's interpretation. It does not establish that Nav2 received
> the observation, transformed it into the relevant frame, inserted it into the costmap used by
> the planner/controller, or changed a decision because of it.

Those links require runtime evidence from the corresponding perception-to-costmap-to-decision
chain, or a declared intervention/model. CRANE should preserve this boundary and should not add a
new VLM/perception workstream merely to match the precedent.

## Manuscript-safe positioning

- “Fernández-Becerra et al. establish ROS/Nav2 accountability pipelines, agentic retrieval over
  structured robot records, source-bearing explanations, hallucination grading, and multimodal
  explanation context as prior art.”
- “CRANE asks a different empirical question: whether independently derived measurements and
  diagnostic computations support a physical or execution mechanism beyond causal statements
  already present in logs, while retaining provenance, conflicts, alternatives, and evidence-
  sufficiency limits.”
- “Faithfulness to a retrieved event record is not equivalent to validating the physical mechanism
  asserted by that record.”
- “Visual observation of an obstacle does not by itself show that Nav2 consumed that observation
  or that it caused a planning or control decision.”
- “Any positive CRANE claim about independently checked diagnosis is provisional and will be made
  only where prospective, scenario-clustered results support it.”

## Claims to avoid

- First/novel ROS-log RAG, ROS/Nav2 black-box accountability, natural-language robot-log
  explanations, source-aware explanations, multimodal/VLM explanation context, agentic RAG, or
  hallucination grading.
- “The ESWA grader verifies the robot's physical cause.” It grades support by retrieved context.
- “An obstacle in a camera frame was used by Nav2” or “the visible obstacle caused replanning”
  without evidence along the relevant runtime chain.
- “CRANE is the first to calculate quantities over robot records.” ESWA reports time aggregation
  and distance calculation; CRANE's narrower concern is validated, independently derived
  diagnostic quantities and their sufficiency.
- “Hundreds of ESWA ablation outputs are hundreds of independent navigation episodes.” The paper
  reports repeated generations/configurations over three scenarios.

## Bibliographic metadata and access notes

1. Laura Fernández-Becerra, Angel Manuel Guerrero-Higueras, Francisco Javier Rodríguez-Lera, and
   Vicente Matellán Olivera. “Generating trustworthy and context-aware explanations for autonomous
   robots using an LLM agent-based RAG architecture.” *Expert Systems with Applications* 325
   (2026), article 132631. DOI
   [10.1016/j.eswa.2026.132631](https://doi.org/10.1016/j.eswa.2026.132631). The version of record is
   dated online 26 April 2026 and is CC BY-NC-ND 4.0. The full published PDF was verified through
   the [University of León repository record](https://hdl.handle.net/10612/28306).
2. Laura Fernández-Becerra, David Sobrín-Hidalgo, Miguel A. González-Santamarta, Ángel Manuel
   Guerrero-Higueras, Francisco J. Rodríguez Lera, and Vicente Matellán Olivera. “Improving
   accountability and explainability in robots through encryption, large language models, and
   visual language models.” *Logic Journal of the IGPL* 34(1), article jzaf016. DOI
   [10.1093/jigpal/jzaf016](https://doi.org/10.1093/jigpal/jzaf016). Crossref records online
   publication on 4 December 2025 and print publication on 27 January 2026 in the 2026
   volume/issue; it records a CC BY-NC-ND 4.0 license. Cite **2025** when treating the work as
   online-first, or **2026** when citing the assigned issue, and keep that choice consistent between
   text and bibliography. The publisher PDF endpoint was blocked and the [University of León
   repository copy](https://hdl.handle.net/10612/27120) was marked embargoed/access-restricted from
   this environment. Consequently, IGPL claims above are limited to the publisher-deposited
   abstract/metadata and author-released code; detailed experimental claims from the inaccessible
   full text are deliberately not asserted.

## Remaining uncertainty

- The IGPL full-text methods and results could not be checked page by page. Before quoting its
  experiments, model comparisons, or numerical results, verify them against the version of record.
- The linkage between the IGPL article and the named GitHub repository is supported by matching
  authorship/topic and the repository's project description, but an explicit repository URL in the
  inaccessible article body was not verified.
- Both software repositories are mutable. Manuscript statements should cite the paper; any
  implementation-specific compatibility check should record a commit hash and environment.
- Neither paper establishes literature-wide limits on physical robot diagnosis. The safe CRANE
  position is a scoped study contribution, not a “first system” claim.
