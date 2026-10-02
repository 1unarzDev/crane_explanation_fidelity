# Contextual attachment records — 2026-09-30

This development interface implements the structural boundary identified in the claim-attachment
inventory. It is not a new explanation method, a semantic qualification, an endpoint mapping or
an annotation execution declaration. No model call, pilot input construction or key join is
authorized. The combined support canary remains `FAILED_SYNTHETIC_REFERENCE_RETAIN_NO_RETRY`;
its frozen references, returns and unlaunched C remain unchanged.

## Inputs and proposals

Inputs contain an opaque answer ID, the exact recorded question, the full unchanged answer and
the ordered atomic inventory. Each atom retains its normalized claim text and exact answer span
with Unicode character offsets. This distinguishes repeated identical strings within an answer.
Do not reconstruct an absent question from the answer or copy a question from another condition.
Obtaining a pilot's blinded question still requires its governed packet construction; this
interface has only been exercised with project-authored synthetic data.

The return binds canonical hashes of the complete input and ontology. Every atom has one proposal
in order, with a contextual proposition, stance, polarity, scope, referent status, proposed match
status, nullable proposed contract, exact contextual quotes and a scope note. At least one quote
must come from that atom's retained answer span. Additional question/answer quotes can support
scope and antecedent interpretation. Hash and span checks establish identity only, not whether
the interpretation is correct. The unchanged atom is never overwritten by the contextual proposal.

The interface does not import A/B role candidates, extractor tags, support labels or raw highest
levels. It cannot express a mechanistic endpoint flag or asserted response rank. Those remain
separate, prospectively validated decisions.

## Structural restrictions

- `PROPOSED_MATCH` requires a known current positive episode contract, a resolved episode scope
  and an asserted or hedged stance. A hedge remains an assertion proposal; it does not become
  automatic abstention. A proposed match is never an adjudicated attachment.
- `OUT_OF_CATALOG` preserves an asserted unmatched proposition, including negative causation and
  source/configuration facts. It cannot borrow a nearby positive contract or disappear through
  `NOT_APPLICABLE`. Its evidential requirements and endpoint treatment remain open.
- `UNRESOLVED` preserves unresolved stance, scope or referent and a null proposed contract. It
  does not invent a referent for “it,” “these causes” or a bare affirmative.
- `NOT_APPLICABLE` may record unendorsed/hypothetical/quoted material or a limitation, retaining
  its text and scope. It is not permission to discard a concrete asserted proposition. Whether
  a sentence is actually unendorsed or a limitation still requires semantic qualification.

Polarity is proposition polarity, not a scan for the word “not.” The catalog's affirmative
command–motion discrepancy proposition itself contains negation (“was not reflected”). A claim
that the discrepancy occurred can therefore affirm that proposition. Negating a positive
catalog proposition cannot attach to its positive evidence contract. The current catalog does
not supply contracts for arbitrary causal negatives. Likewise, “recovery did not cause success”
must remain distinct from “recovery does not establish success.” These are proposed semantic
interpretations to qualify, not meanings the structural validator can discover.

## Verification scope and remaining gates

The validator checks exact fields, context/ontology hashes, item order and identity, known
contract IDs, category compatibility, exact character offsets and own-atom citations. It rejects
support/rank/role fields and returns all semantic, mechanistic, rank, endpoint and execution
authorization flags false. The companion JSON schemas specify the transport shape; cross-field,
hash and offset restrictions are enforced by the validator.

Synthetic tests exercise changed questions/answers, altered ontology, endorsed hedges, negative
causation, limitations, unendorsed quotes, source facts, unresolved referents, repeated spans,
missing/reordered atoms and rank injection. These are offline interface tests, not annotation
accuracy, automated agreement, human validation or independent experimental samples. They do
not settle any retained pilot atom's meaning.

The bound candidate declaration authorizes zero calls and records this limited scope. Future
semantic qualification must prospectively cover these distinctions and disagreements, preserve
the failed combined support gate, and establish how unmatched/unresolved propositions and
family-local abstractions enter the episode endpoint. No such qualification or endpoint policy
is selected here. Support measurement, disagreement-only adjudication, an authorized key join,
fresh aligned B0–B4 development evidence, coverage/discordances, power and compatible physical
allocation still precede P11. All previously required comparisons and reporting remain required.

Run `python analysis/validate_evidence_calibration_claim_attachment.py` for the read-only candidate
declaration/hash audit. The command accepts no pilot packet and makes no model invocation. The
Python `validate` function accepts supplied proposals for structural checks only.
