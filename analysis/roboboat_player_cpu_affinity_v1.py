#!/usr/bin/python3
"""Operational development wrapper: unchanged rendered player on CPUs 0–15."""
import hashlib
import os
from pathlib import Path
import sys

PLAYER = Path('/home/lunarz/worktrees/roboboat-docking/packages/crane_ml/Builds/CRANE-RoboBoat-Bow/CRANE.x86_64')
PLAYER_SHA256 = 'a7ad5b156bd9a1232544ff6fc12e5f863d8f1f2348c5b141f5c3d4230e5be292'
CPUSET = frozenset(range(16))


def launch(arguments):
    if not CPUSET <= os.sched_getaffinity(0):
        raise RuntimeError('declared CPU affinity unavailable')
    with PLAYER.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest() != PLAYER_SHA256:
            raise RuntimeError('bound physical player changed')
    os.sched_setaffinity(0,CPUSET)
    if os.sched_getaffinity(0) != CPUSET:
        raise RuntimeError('CPU affinity not applied')
    print('RoboBoat development CPU affinity applied: 0-15; physical player hash verified.',file=sys.stderr,flush=True)
    os.execv(str(PLAYER),[str(PLAYER),*arguments])


if __name__=='__main__':launch(sys.argv[1:])
