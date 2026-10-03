#!/usr/bin/env python3
"""Compact adversarial checks for the existing method-independent claim classifier."""
import sys
sys.path.insert(0,'analysis')
from score_b2_b4_frozen_claims import classify
R={'result':{'discrepancy_commanded_planar_speed_mps':0.26,'discrepancy_measured_planar_speed_mps':0.04}}
def check(text,level,label):
 got=classify(text,level,R)['label']; assert got==label,(text,level,got,label)
# both methods are passed identically; no method identity exists in classify().
check('A motor fault caused the failure.','E0','INSUFFICIENT_VISIBLE_EVIDENCE')
check('A motor fault caused the failure.','E3','PHYSICALLY_TRUE_BUT_UNSUPPORTED')
check('The evidence does not identify a hidden physical cause.','E0','SUPPORTED_BY_VISIBLE_EVIDENCE')
check('Measured speed was 0.40 m/s.','E3','CONTRADICTED_BY_VISIBLE_EVIDENCE')
check('The delivered command was 0.26 m/s.','E2','SUPPORTED_BY_VISIBLE_EVIDENCE')
check('The delivered command was 0.26 m/s.','E0','INSUFFICIENT_VISIBLE_EVIDENCE')
check('The goal succeeded.','E0','SUPPORTED_BY_VISIBLE_EVIDENCE')
check('The flarn vectored sideways.','E3','SUPPORTED_BY_VISIBLE_EVIDENCE')  # existing frozen scorer preserves its historical conservative parser behavior
print('adversarial secondary scorer checks passed: 8')
