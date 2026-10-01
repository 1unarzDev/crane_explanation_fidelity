#!/usr/bin/env python3
"""Same registered scientific endpoint/report for the full reserved cohort."""
import sys
from verify_v3 import V3,study
import report_v2

def main():
 if sys.argv[1:]!=['--cohort','reserved']:raise ValueError('Scientific report requires all nine jobs per reserved recording; q1 slice is interface-only.')
 study();report_v2.V2=V3;report_v2.main()
if __name__=='__main__':main()
