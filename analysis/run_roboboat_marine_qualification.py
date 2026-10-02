#!/usr/bin/env python3
"""Apply the current qualified prompt/schema with a separate bounded marine suite."""
import json
from pathlib import Path
from run_evidence_calibration_agent_annotation import StructuredCodexCliAgentCaller
from run_evidence_calibration_agent_qualification import run
from roboboat_isolated_transport import isolated_run
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    doc=ROOT/'docs/roboboat_terminal_evidence'
    result=run(doc/'marine_qualification_suite_v1.json',doc/'marine_qualification_freeze_v2.json',ROOT/'artifacts/roboboat-terminal-v1/qualification-v2',
      caller_factory=lambda cache:StructuredCodexCliAgentCaller(cache,model='gpt-6-astra',effort='high',runner=isolated_run))
    print(result['status'],flush=True)
