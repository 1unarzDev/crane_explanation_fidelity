#!/usr/bin/env bash
set -euo pipefail

# Exercise the diagnostic annotation/adjudication/key-join/summary path without
# creating human labels or writing to governed study locations.

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd "${script_dir}/.." && pwd)"
cd "${workspace_root}"

inventory="manifests/annotation/diagnostic-development-pilot-v1.json"
scratch_root="$(mktemp -d "${TMPDIR:-/tmp}/crane-diagnostic-pipeline.XXXXXX")"
expected_responses="$(jq -r '.responses' "${inventory}")"
expected_clusters="$(jq -r '.statistical_clusters' "${inventory}")"
expected_packets="$(jq -r '.packets | length' "${inventory}")"
join_args=()

while IFS=$'\t' read -r packet_name packet_path; do
  for annotator in a b; do
    python analysis/build_diagnostic_annotation_form.py \
      --packet "${packet_path}" \
      --output "${scratch_root}/${packet_name}-${annotator}-blank.jsonl" \
      --annotator-id "synthetic-${annotator}" >/dev/null
    jq -c '
      .supported_diagnostic_success = false
      | .material_error = false
      | .error_categories = []
      | .required_units_correct = .required_units_total
      | .mechanism_correct = true
      | .failure_chain_correct = true
      | .qualification_correct = true
      | .causal_overclaim = false
      | .unnecessary_abstention = false
      | .evidence_citations_correct = true
      | .next_check_correct = true
      | .evidence_problem = false
      | .rationale = "SYNTHETIC PIPELINE REHEARSAL ONLY - NOT A HUMAN LABEL"
    ' "${scratch_root}/${packet_name}-${annotator}-blank.jsonl" \
      > "${scratch_root}/${packet_name}-${annotator}.jsonl"
  done

  python analysis/adjudicate_diagnostic_annotations.py \
    --packet "${packet_path}" \
    --annotator-a "${scratch_root}/${packet_name}-a.jsonl" \
    --annotator-b "${scratch_root}/${packet_name}-b.jsonl" \
    --output "${scratch_root}/${packet_name}-adjudicated.json" >/dev/null
  join_args+=(--adjudication "${packet_name}=${scratch_root}/${packet_name}-adjudicated.json")
done < <(jq -r '.packets[] | [.name, .packet] | @tsv' "${inventory}")

python analysis/join_diagnostic_annotation_keys.py \
  --inventory "${inventory}" \
  "${join_args[@]}" \
  --output "${scratch_root}/joined.jsonl" \
  --report "${scratch_root}/join-report.json" >/dev/null
python analysis/summarize_diagnostic_development.py \
  "${scratch_root}/joined.jsonl" \
  --output "${scratch_root}/summary.json" >/dev/null

jq -e \
  --argjson responses "${expected_responses}" \
  --argjson clusters "${expected_clusters}" \
  '.status == "COMPLETE_DEVELOPMENT_ONLY"
   and .input_responses == $responses
   and .analysis_responses == $responses
   and .input_statistical_clusters == $clusters
   and .analysis_statistical_clusters == $clusters
   and (.quarantined_statistical_clusters | length) == 0' \
  "${scratch_root}/join-report.json" >/dev/null
jq -e \
  --argjson responses "${expected_responses}" \
  --argjson clusters "${expected_clusters}" \
  --argjson packets "${expected_packets}" \
  '.status == "DEVELOPMENT_ONLY_NOT_INFERENTIAL"
   and .responses == $responses
   and .statistical_clusters == $clusters
   and .conditions.P.responses == $packets
   and .conditions.P.template_fallback_rate == 1.0' \
  "${scratch_root}/summary.json" >/dev/null

# Verify fail-closed whole-cluster quarantine using the first inventory packet.
quarantine_name="$(jq -r '.packets[0].name' "${inventory}")"
quarantine_cluster="$(jq -r '.packets[0].statistical_cluster_id' "${inventory}")"
first_id="$(jq -r '.labels | keys[0]' "${scratch_root}/${quarantine_name}-adjudicated.json")"
jq --arg id "${first_id}" \
  '.labels[$id].evidence_problem = true | .evidence_problem_quarantined_responses = [$id]' \
  "${scratch_root}/${quarantine_name}-adjudicated.json" \
  > "${scratch_root}/${quarantine_name}-adjudicated-quarantine.json"

quarantine_join_args=()
removed_responses=0
while IFS=$'\t' read -r packet_name packet_path packet_cluster; do
  adjudication_path="${scratch_root}/${packet_name}-adjudicated.json"
  if [[ "${packet_name}" == "${quarantine_name}" ]]; then
    adjudication_path="${scratch_root}/${packet_name}-adjudicated-quarantine.json"
  fi
  if [[ "${packet_cluster}" == "${quarantine_cluster}" ]]; then
    packet_rows="$(wc -l < "${packet_path}")"
    removed_responses=$((removed_responses + packet_rows))
  fi
  quarantine_join_args+=(--adjudication "${packet_name}=${adjudication_path}")
done < <(jq -r '.packets[] | [.name, .packet, .statistical_cluster_id] | @tsv' "${inventory}")

python analysis/join_diagnostic_annotation_keys.py \
  --inventory "${inventory}" \
  "${quarantine_join_args[@]}" \
  --output "${scratch_root}/joined-quarantine.jsonl" \
  --report "${scratch_root}/join-report-quarantine.json" >/dev/null

expected_after_quarantine=$((expected_responses - removed_responses))
expected_clusters_after_quarantine=$((expected_clusters - 1))
jq -e \
  --arg cluster "${quarantine_cluster}" \
  --argjson responses "${expected_responses}" \
  --argjson remaining "${expected_after_quarantine}" \
  --argjson clusters "${expected_clusters_after_quarantine}" \
  --argjson removed "${removed_responses}" \
  '.input_responses == $responses
   and .analysis_responses == $remaining
   and .analysis_statistical_clusters == $clusters
   and .quarantined_statistical_clusters == [$cluster]
   and .quarantined_responses == $removed' \
  "${scratch_root}/join-report-quarantine.json" >/dev/null

jq '{status, input_responses, analysis_responses, input_statistical_clusters,
     analysis_statistical_clusters, quarantined_statistical_clusters}' \
  "${scratch_root}/join-report.json"
jq '{responses, statistical_clusters, diagnosable_responses, ambiguous_responses,
     p_template_fallback_rate: .conditions.P.template_fallback_rate}' \
  "${scratch_root}/summary.json"
jq '{analysis_responses, analysis_statistical_clusters,
     quarantined_statistical_clusters, quarantined_responses}' \
  "${scratch_root}/join-report-quarantine.json"
printf 'Synthetic rehearsal artifacts: %s\n' "${scratch_root}"
