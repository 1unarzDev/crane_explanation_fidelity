#!/usr/bin/env python3
"""Print development responses beside their allowed evidence, for unblinded control annotation.

The model-strength control requires a human-readable pass over development responses. This lays
each response next to the runtime facts an annotator must check it against, so the rubric is
applied to evidence rather than to recollection.

It refuses sealed roots outright. Sealed answers in either arm are not inspected until the blinded
dual-annotation workflow runs, and a convenience viewer is exactly the tool that would erode that
rule by accident.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
SEALED_ROOTS = ("model_outputs/final", "model_outputs/replication-claude")
MODEL_CONDITIONS = ("F", "G", "H")


def refuse_sealed(root: Path) -> None:
    relative = root.relative_to(WORKSPACE).as_posix()
    for sealed in SEALED_ROOTS:
        if relative == sealed or relative.startswith(sealed + "/"):
            raise SystemExit(
                f"refusing to display sealed responses under {sealed}; "
                "sealed answers are scored only through the blinded annotation workflow"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-root", required=True, type=Path)
    parser.add_argument("--episode")
    parser.add_argument("--question-kind")
    parser.add_argument(
        "--evidence", action="store_true", help="also print the retained parity record"
    )
    parser.add_argument("--full", action="store_true", help="print whole responses, not excerpts")
    args = parser.parse_args()

    root = (WORKSPACE / args.result_root).resolve()
    refuse_sealed(root)
    if not root.is_dir():
        raise SystemExit(f"missing result root: {root}")

    for path in sorted(root.rglob("*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        if args.episode and args.episode not in result["episode_id"]:
            continue
        if args.question_kind and result["question_kind"] != args.question_kind:
            continue
        print("=" * 100)
        print(
            f"{result['episode_id']}  {result['question_kind']}  "
            f"model={result['model']}  status={result['status']}"
        )
        print(f"Q: {result['question']}")
        if args.evidence:
            print(f"parity: {json.dumps(result['information_parity'], sort_keys=True)}")
        for output in result["outputs"]:
            if output["condition"] not in MODEL_CONDITIONS:
                continue
            print("-" * 100)
            print(f"[{output['condition']}]", end="")
            if output["condition"] == "G":
                print(
                    f"  verification_accepted={output['verification_accepted']}"
                    f"  template_fallback={output['used_template_fallback']}"
                )
            else:
                print()
            text = output["text"]
            print(text if args.full else text[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
