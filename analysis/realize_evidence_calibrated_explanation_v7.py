"""Preserve supported software observations in B4's local nonterminal fallback."""
from realize_evidence_calibrated_explanation_v6 import realize as previous

VERSION = "v7-development-nonterminal-trace-retention"


def realize(ontology, entry, question_contract):
    output = previous(ontology, entry, question_contract)
    evidence = entry["method_packet"]["evidence"]
    trace = evidence.get("behavior_tree_transitions", {}).get("execution_sequence")
    anchors = evidence.get("source_anchors", {})
    if trace and anchors and not any(c["clause_id"] == "software-execution-trace" for c in output["clauses"]):
        counts = [trace.get(k) for k in ("follow_path_attempt_count", "follow_path_failure_count", "source_qualified_wait_recovery_count")]
        classifier = trace.get("recovery_node_classifier", {})
        if (all(type(x) is int and x >= 0 for x in counts) and counts[1] <= counts[0]
                and classifier.get("policy_sha256") == anchors.get("bt_policy_sha256")
                and classifier.get("node_name") == "Wait"):
            output["clauses"] = [c for c in output["clauses"] if c["clause_id"] != "missing-trace-limitation"]
            output["clauses"].append(dict(clause_id="software-execution-trace",contract_id="software-execution-trace",
                kind="PACKET_DERIVED", support_references=["recovery-trace","source-anchors"],
                text=f"The retained trace records {counts[0]} FollowPath attempts, {counts[1]} FollowPath failures, and {counts[2]} source-qualified Wait recovery invocations. These observations do not prove the unobserved history or identify a physical cause or recovery causation."))
    output.update(version=VERSION,schema="crane-evidence-calibration-b4-development-output/v7",
                  development_change="Retain available source-qualified software observations in local nonterminal fallback",
                  answer=" ".join(c["text"] for c in output["clauses"]))
    return output
