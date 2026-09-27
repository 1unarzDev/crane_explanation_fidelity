#!/usr/bin/env python3
"""Run one development P-contract-v4/R-contract pair without changing older runners."""

from __future__ import annotations

import run_contract_complete_response_pair as base
from compose_contract_complete_answer_v4 import compile_answer


def main() -> int:
    base.compile_answer = compile_answer
    base.run(base.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
