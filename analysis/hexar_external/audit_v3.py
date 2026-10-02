#!/usr/bin/env python3
"""Same inventory/numerical audits under the qualified versioned root."""
import argparse,sys
from verify_v3 import V3,qualified,study
import audit_inventory_v2,numerical_audit_v2

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=['development','reserved'],required=True);a=ap.parse_args();qualified()
 if a.cohort=='reserved':study()
 for module in (audit_inventory_v2,numerical_audit_v2):module.V2=V3;module.main()
if __name__=='__main__':main()
