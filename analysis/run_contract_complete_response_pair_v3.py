#!/usr/bin/env python3
"""Run a development P-contract-v3/R-contract pair without modifying the v2 runner."""

from __future__ import annotations

import run_contract_complete_response_pair as base
from compose_contract_complete_answer_v3 import compile_answer


def main() -> int:
    base.compile_answer = compile_answer
    base.run(base.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
