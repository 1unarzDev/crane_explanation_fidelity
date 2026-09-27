#!/usr/bin/env python3
"""Run one inspected-case P-contract-v5/R-contract-concise development pair."""

from __future__ import annotations

import run_contract_complete_response_pair as base
from compose_contract_complete_answer_v5 import compile_answer


base.compile_answer = compile_answer
base.PROMPT = base.ROOT / (
    "research/explanation_fidelity/prompts/"
    "diagnostic_repository_agent_contract_complete_concise_v1.txt"
)
base.PAIR_STATUS = "DEVELOPMENT_ONLY_NOT_CONFIRMATORY"
base.BASELINE_ID = "r-contract-concise-v1-development"
base.CAMPAIGN_ID = "contract-complete-concise-development-v1"


def main() -> int:
    base.run(base.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
