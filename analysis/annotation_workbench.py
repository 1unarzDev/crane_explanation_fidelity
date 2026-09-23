#!/usr/bin/env python3
"""Interactive, resumable data-entry helper for blinded JSONL annotation forms."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable


LEGACY_ERROR_CATEGORIES = (
    "unsupported_fact",
    "contradicted_fact",
    "incorrect_identifier",
    "incorrect_count",
    "incorrect_status",
    "incorrect_comparison",
    "incorrect_source_attribution",
    "incorrect_runtime_source_link",
    "unsupported_mechanism_detail",
    "unsupported_causal_diagnosis",
    "unsupported_counterfactual",
    "incorrect_explanatory_relationship",
    "false_premise_acceptance",
    "incorrect_completeness",
)
DIAGNOSTIC_ERROR_CATEGORIES = (
    "unsupported_fact",
    "contradicted_fact",
    "incorrect_measurement",
    "incorrect_mechanism",
    "incorrect_failure_chain",
    "unsupported_causal_claim",
    "unsupported_identity",
    "incorrect_completeness",
    "incorrect_source_link",
    "false_premise_acceptance",
    "unsupported_counterfactual",
)
DIAGNOSTIC_FIELDS = frozenset(
    {
        "response_id",
        "annotator_id",
        "supported_diagnostic_success",
        "material_error",
        "error_categories",
        "required_units_total",
        "required_units_correct",
        "mechanism_correct",
        "failure_chain_correct",
        "qualification_correct",
        "causal_overclaim",
        "unnecessary_abstention",
        "evidence_citations_correct",
        "next_check_correct",
        "evidence_problem",
        "rationale",
    }
)
LEGACY_FIELDS = frozenset(
    {
        "response_id",
        "episode_id",
        "scenario_family",
        "question_kind",
        "condition_blinded_id",
        "material_error",
        "error_categories",
        "disposition",
        "substantive_answer",
        "requested_conclusion_answerable",
        "correct_abstention",
        "answerable_units_total",
        "answerable_units_correct",
        "claim_count",
        "unsupported_claim_count",
        "source_reference_count",
        "correct_source_reference_count",
        "source_references_total_answerable",
        "physical_evidence_claim_count",
        "correct_physical_evidence_claim_count",
        "causal_overclaim",
        "qualification_correct",
        "evidence_problem",
        "annotator_id",
        "rationale",
    }
)
DIAGNOSTIC_BOOLEAN_FIELDS = (
    "supported_diagnostic_success",
    "material_error",
    "mechanism_correct",
    "failure_chain_correct",
    "qualification_correct",
    "causal_overclaim",
    "unnecessary_abstention",
    "evidence_citations_correct",
    "next_check_correct",
    "evidence_problem",
)
LEGACY_BOOLEAN_FIELDS = (
    "material_error",
    "substantive_answer",
    "requested_conclusion_answerable",
    "correct_abstention",
    "causal_overclaim",
    "qualification_correct",
    "evidence_problem",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} line {line_number} is not an object")
        rows.append(value)
    if not rows:
        raise ValueError(f"{path} is empty")
    return rows


def detect_rubric(form_row: dict[str, Any]) -> str:
    fields = frozenset(form_row)
    if fields == DIAGNOSTIC_FIELDS:
        return "diagnostic"
    if fields == LEGACY_FIELDS:
        return "legacy"
    raise ValueError("form does not match the diagnostic or legacy rubric")


def require_boolean_fields(row: dict[str, Any], fields: tuple[str, ...], identifier: str) -> None:
    invalid = [field for field in fields if not isinstance(row[field], bool)]
    if invalid:
        raise ValueError(f"resume output has non-boolean fields for {identifier}: {invalid}")


def require_bounded_count(
    row: dict[str, Any], field: str, identifier: str, *, maximum_field: str | None = None
) -> None:
    value = row[field]
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"resume output has invalid count {field} for {identifier}")
    if maximum_field is not None and value > row[maximum_field]:
        raise ValueError(
            f"resume output has {field} greater than {maximum_field} for {identifier}"
        )


def validate_completed_row(row: dict[str, Any], rubric: str, identifier: str) -> None:
    if any(value is None for value in row.values()):
        raise ValueError(f"resume output contains an incomplete row: {identifier}")
    if not isinstance(row["annotator_id"], str) or not row["annotator_id"].strip():
        raise ValueError(f"resume output has an empty annotator_id for {identifier}")
    if not isinstance(row["rationale"], str) or not row["rationale"].strip():
        raise ValueError(f"resume output has an empty rationale for {identifier}")

    categories = row["error_categories"]
    allowed_categories = (
        DIAGNOSTIC_ERROR_CATEGORIES if rubric == "diagnostic" else LEGACY_ERROR_CATEGORIES
    )
    if (
        not isinstance(categories, list)
        or not all(isinstance(category, str) for category in categories)
        or len(categories) != len(set(categories))
        or any(category not in allowed_categories for category in categories)
    ):
        raise ValueError(f"resume output has invalid error_categories for {identifier}")
    if row["material_error"] != bool(categories):
        raise ValueError(f"resume output has inconsistent material-error categories for {identifier}")

    if rubric == "diagnostic":
        require_boolean_fields(row, DIAGNOSTIC_BOOLEAN_FIELDS, identifier)
        require_bounded_count(
            row,
            "required_units_correct",
            identifier,
            maximum_field="required_units_total",
        )
        if row["supported_diagnostic_success"] and (
            row["material_error"] or not row["mechanism_correct"]
        ):
            raise ValueError(
                f"resume output has inconsistent supported diagnostic success for {identifier}"
            )
        return

    require_boolean_fields(row, LEGACY_BOOLEAN_FIELDS, identifier)
    if row["disposition"] not in {"full", "partial", "abstained", "nonanswer"}:
        raise ValueError(f"resume output has invalid disposition for {identifier}")
    if row["substantive_answer"] != (row["disposition"] in {"full", "partial"}):
        raise ValueError(f"resume output has inconsistent substantive_answer for {identifier}")
    for field, maximum in (
        ("answerable_units_correct", "answerable_units_total"),
        ("claim_count", None),
        ("unsupported_claim_count", "claim_count"),
        ("source_reference_count", None),
        ("correct_source_reference_count", "source_reference_count"),
        ("source_references_total_answerable", None),
        ("physical_evidence_claim_count", None),
        ("correct_physical_evidence_claim_count", "physical_evidence_claim_count"),
    ):
        require_bounded_count(row, field, identifier, maximum_field=maximum)


def prompt_bool(prompt: str, ask: Callable[[str], str]) -> bool:
    while True:
        value = ask(f"{prompt} [y/n]: ").strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Enter y or n.")


def prompt_int(
    prompt: str, ask: Callable[[str], str], *, minimum: int = 0, maximum: int | None = None
) -> int:
    while True:
        value = ask(f"{prompt}: ").strip()
        try:
            number = int(value)
        except ValueError:
            print("Enter an integer.")
            continue
        if number < minimum or (maximum is not None and number > maximum):
            suffix = f" through {maximum}" if maximum is not None else " or greater"
            print(f"Enter {minimum}{suffix}.")
            continue
        return number


def prompt_choice(prompt: str, choices: tuple[str, ...], ask: Callable[[str], str]) -> str:
    options = ", ".join(f"{index + 1}={choice}" for index, choice in enumerate(choices))
    while True:
        value = ask(f"{prompt} [{options}]: ").strip()
        if value in choices:
            return value
        try:
            index = int(value) - 1
        except ValueError:
            index = -1
        if 0 <= index < len(choices):
            return choices[index]
        print("Enter a listed number or exact value.")


def prompt_categories(
    categories: tuple[str, ...], ask: Callable[[str], str]
) -> list[str]:
    print("Material-error categories:")
    for index, category in enumerate(categories, 1):
        print(f"  {index:2d}. {category}")
    while True:
        raw = ask("Comma-separated category numbers: ").strip()
        try:
            indexes = [int(value.strip()) - 1 for value in raw.split(",") if value.strip()]
        except ValueError:
            indexes = []
        if indexes and len(indexes) == len(set(indexes)) and all(
            0 <= index < len(categories) for index in indexes
        ):
            return [categories[index] for index in indexes]
        print("Select at least one valid category without duplicates.")


def prompt_rationale(ask: Callable[[str], str]) -> str:
    while True:
        value = ask("Concise evidence-based rationale: ").strip()
        if value:
            return value
        print("Rationale must not be empty.")


def complete_diagnostic(template: dict[str, Any], ask: Callable[[str], str]) -> dict[str, Any]:
    row = dict(template)
    row["material_error"] = prompt_bool("Material error", ask)
    row["error_categories"] = (
        prompt_categories(DIAGNOSTIC_ERROR_CATEGORIES, ask) if row["material_error"] else []
    )
    row["required_units_correct"] = prompt_int(
        "Required units correct",
        ask,
        maximum=row["required_units_total"],
    )
    row["mechanism_correct"] = prompt_bool("Mechanism correct", ask)
    row["failure_chain_correct"] = prompt_bool("Failure chain correct", ask)
    row["qualification_correct"] = prompt_bool("Qualification/limits correct", ask)
    row["causal_overclaim"] = prompt_bool("Causal overclaim", ask)
    row["unnecessary_abstention"] = prompt_bool("Unnecessary abstention", ask)
    row["evidence_citations_correct"] = prompt_bool("Evidence citations correct", ask)
    row["next_check_correct"] = prompt_bool("Next diagnostic check correct", ask)
    row["evidence_problem"] = prompt_bool("Evidence/question/reference problem", ask)
    row["supported_diagnostic_success"] = prompt_bool("Supported diagnostic success", ask)
    if row["supported_diagnostic_success"] and (
        row["material_error"] or not row["mechanism_correct"]
    ):
        raise ValueError(
            "supported diagnostic success requires no material error and a correct mechanism"
        )
    row["rationale"] = prompt_rationale(ask)
    return row


def complete_legacy(template: dict[str, Any], ask: Callable[[str], str]) -> dict[str, Any]:
    row = dict(template)
    row["material_error"] = prompt_bool("Material error", ask)
    row["error_categories"] = (
        prompt_categories(LEGACY_ERROR_CATEGORIES, ask) if row["material_error"] else []
    )
    row["disposition"] = prompt_choice(
        "Response disposition", ("full", "partial", "abstained", "nonanswer"), ask
    )
    row["substantive_answer"] = row["disposition"] in {"full", "partial"}
    print(f"substantive_answer={str(row['substantive_answer']).lower()} (from disposition)")
    row["requested_conclusion_answerable"] = prompt_bool(
        "Requested conclusion answerable", ask
    )
    row["correct_abstention"] = prompt_bool("Correct abstention", ask)
    row["answerable_units_correct"] = prompt_int(
        "Answerable units correct", ask, maximum=row["answerable_units_total"]
    )
    row["claim_count"] = prompt_int("Claim count", ask)
    row["unsupported_claim_count"] = prompt_int(
        "Unsupported claim count", ask, maximum=row["claim_count"]
    )
    row["source_reference_count"] = prompt_int("Source-reference count", ask)
    row["correct_source_reference_count"] = prompt_int(
        "Correct source-reference count", ask, maximum=row["source_reference_count"]
    )
    row["source_references_total_answerable"] = prompt_int(
        "Total answerable source references", ask
    )
    row["physical_evidence_claim_count"] = prompt_int("Physical-evidence claim count", ask)
    row["correct_physical_evidence_claim_count"] = prompt_int(
        "Correct physical-evidence claim count",
        ask,
        maximum=row["physical_evidence_claim_count"],
    )
    row["causal_overclaim"] = prompt_bool("Causal overclaim", ask)
    row["qualification_correct"] = prompt_bool("Qualification/limits correct", ask)
    row["evidence_problem"] = prompt_bool("Evidence/question/reference problem", ask)
    row["rationale"] = prompt_rationale(ask)
    return row


def validate_resume(
    form_rows: list[dict[str, Any]], completed_rows: list[dict[str, Any]], rubric: str
) -> dict[str, dict[str, Any]]:
    form_by_id = {row.get("response_id"): row for row in form_rows}
    if len(form_by_id) != len(form_rows) or None in form_by_id:
        raise ValueError("form has missing or duplicate response IDs")
    completed: dict[str, dict[str, Any]] = {}
    prefilled = (
        {"response_id", "annotator_id", "required_units_total"}
        if rubric == "diagnostic"
        else {
            "response_id",
            "episode_id",
            "scenario_family",
            "question_kind",
            "condition_blinded_id",
            "answerable_units_total",
            "annotator_id",
        }
    )
    for row in completed_rows:
        identifier = row.get("response_id")
        if identifier not in form_by_id or identifier in completed:
            raise ValueError("resume output has an unknown or duplicate response ID")
        template = form_by_id[identifier]
        if set(row) != set(template):
            raise ValueError(f"resume output changed the field inventory for {identifier}")
        for field in prefilled:
            if row.get(field) != template.get(field):
                raise ValueError(f"resume output changed prefilled field {field} for {identifier}")
        validate_completed_row(row, rubric, identifier)
        completed[identifier] = row
    return completed


def atomic_write(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as stream:
        temporary = Path(stream.name)
        for row in rows:
            stream.write(json.dumps(row) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def run_workbench(
    packet_rows: list[dict[str, Any]],
    form_rows: list[dict[str, Any]],
    completed_rows: list[dict[str, Any]],
    *,
    output: Path,
    ask: Callable[[str], str] = input,
) -> tuple[int, int]:
    if len(packet_rows) != len(form_rows):
        raise ValueError("packet and form row counts differ")
    rubric = detect_rubric(form_rows[0])
    if any(detect_rubric(row) != rubric for row in form_rows):
        raise ValueError("form mixes diagnostic and legacy rubric rows")
    if any(
        not isinstance(row["annotator_id"], str) or not row["annotator_id"].strip()
        for row in form_rows
    ):
        raise ValueError("form must carry one non-empty annotator_id")
    if len({row["annotator_id"] for row in form_rows}) != 1:
        raise ValueError("form carries multiple annotator IDs")
    completed = validate_resume(form_rows, completed_rows, rubric)
    packet_by_id = {row.get("response_id"): row for row in packet_rows}
    if set(packet_by_id) != {row["response_id"] for row in form_rows}:
        raise ValueError("packet and form response inventories differ")

    for index, template in enumerate(form_rows, 1):
        identifier = template["response_id"]
        if identifier in completed:
            continue
        print("\n" + "=" * 80)
        print(f"Response {index}/{len(form_rows)} | opaque ID {identifier}")
        print(json.dumps(packet_by_id[identifier], indent=2, ensure_ascii=False))
        if ask("Press Enter to annotate, or q to save and quit: ").strip().lower() == "q":
            break
        while True:
            try:
                row = (
                    complete_diagnostic(template, ask)
                    if rubric == "diagnostic"
                    else complete_legacy(template, ask)
                )
            except ValueError as error:
                print(f"Row rejected: {error}. Re-enter this response.")
                continue
            if prompt_bool("Save this completed judgment", ask):
                completed[identifier] = row
                ordered = [
                    completed[item["response_id"]]
                    for item in form_rows
                    if item["response_id"] in completed
                ]
                atomic_write(output, ordered)
                break
            print("Judgment discarded; re-enter this response.")

    print(f"Completed {len(completed)}/{len(form_rows)} responses. Output: {output}")
    return len(completed), len(form_rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--form", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    form = args.form.resolve(strict=True)
    output = args.output.resolve()
    if output in {packet, form}:
        parser.error("--output must differ from --packet and --form")
    if "evaluator_only" in output.parts:
        parser.error("--output must not be under an evaluator_only directory")
    existing = read_jsonl(output) if output.exists() else []
    try:
        run_workbench(
            read_jsonl(packet), read_jsonl(form), existing, output=output
        )
    except ValueError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
