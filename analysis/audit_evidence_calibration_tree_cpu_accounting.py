#!/usr/bin/env python3
"""Revalidate retained fixed accounting bytes; never launch or rewrite a transaction."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evidence_calibration_mcp_stdio_v3 import strict_json
from observe_evidence_calibration_cgroup_limits import write_once
from observe_evidence_calibration_tree_cpu_accounting_v3 import validate_observation


def audit(terminal_path: Path, output_path: Path) -> dict:
    raw = terminal_path.read_bytes()
    terminal = strict_json(raw)
    if (terminal['schema'] != 'crane-tree-cpu-accounting-terminal/v2-development'
            or terminal['status'] != 'TECHNICAL_FAILURE'
            or terminal['error'] != 'retained accounting lacks successful empty process tree'
            or terminal['cleanup']['final_state']['return_code'] != 0
            or terminal['cleanup']['final_state']['stdout'].strip() != 'not-found'):
        raise ValueError('unexpected retained disposition or cleanup; no relaunch')
    validate_observation(terminal['observation'], terminal['samples'])
    result = {'schema': 'crane-tree-cpu-accounting-correction/v1-development',
              'status': 'PASS_RETAINED_ACCOUNTING_EXPECTATION_CORRECTION_NO_RELAUNCH',
              'original_transaction_status': terminal['status'],
              'terminal_sha256': hashlib.sha256(raw).hexdigest(),
              'validator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'corrected_observer_sha256': hashlib.sha256(Path(__file__).with_name(
                  'observe_evidence_calibration_tree_cpu_accounting_v3.py').read_bytes()).hexdigest(),
              'retained_service_cpu_nanoseconds': terminal['samples'][-1]['CPUUsageNSec'],
              'kernel_after_usage_microseconds': terminal['observation']['after']['usage_usec'],
              'descendant_work_cpu_seconds': sum(child['cpu_seconds'] for child in terminal['observation']['children']),
              'parent_work_cpu_seconds': terminal['observation']['parent_work_cpu_seconds'],
              'post_exit_cgroup_retained': False, 'tasks_current_measured_as_zero': False,
              'cumulative_budget_enforced': False, 'model_call_attempted': False,
              'transaction_relaunched': False}
    write_once(output_path, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.terminal, args.output), indent=2))


if __name__ == '__main__':
    main()
