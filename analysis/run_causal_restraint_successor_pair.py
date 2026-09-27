#!/usr/bin/env python3
"""Run one isolated P-contract-v3/R-contract causal-restraint successor pair."""

from __future__ import annotations

from pathlib import Path

import run_contract_complete_response_pair as base
from compose_contract_complete_answer_v3 import compile_answer


base.compile_answer = compile_answer
base.PROMPT = base.ROOT / (
    "research/explanation_fidelity/prompts/"
    "diagnostic_repository_agent_causal_restraint_v1.txt"
)
base.PAIR_STATUS = "PROSPECTIVE_CAUSAL_RESTRAINT_SUCCESSOR"
base.BASELINE_ID = "r-contract-causal-restraint-v1"
base.CAMPAIGN_ID = "explicit-causal-restraint-successor-v1"


def main() -> int:
    base.run(base.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
