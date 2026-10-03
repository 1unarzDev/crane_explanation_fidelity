#!/usr/bin/env python3
"""Audit retained Nav2 capture evidence without treating action success as docking."""
import argparse
import base64
import hashlib
import gzip
import json
import math
from pathlib import Path


def qualified(sample):
    return all((sample.get('hullInsideDockRegion') is True,
                sample.get('xyError', math.inf) <= .40,
                abs(sample.get('yawError', math.inf)) <= .35,
                abs(sample.get('bodySpeed', math.inf)) <= .05,
                abs(sample.get('bodyYawRate', math.inf)) <= .05,
                sample.get('prohibitedContactCount') == 0,
                sample.get('minimumRegionClearance', -math.inf) >= 0))


def inside_first_slip(sample):
    """Project the measured rectangular hull into inspected Unity slip bounds."""
    yaw = sample.get('yaw', math.inf)
    if not math.isfinite(yaw):
        return False
    half_x = abs(math.sin(yaw)) * .5315 + abs(math.cos(yaw)) * .4475
    half_z = abs(math.cos(yaw)) * .5315 + abs(math.sin(yaw)) * .4475
    x, z = -sample['y'], sample['x']
    return (16.337 <= x - half_x and x + half_x <= 18.837
            and .114 <= z - half_z and z + half_z <= 1.614)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    if path.exists():
        return json.loads(path.read_text())
    return json.loads(gzip.decompress(path.with_suffix(path.suffix + '.gz').read_bytes()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    parser.add_argument('--images', action='store_true')
    parser.add_argument('--first-dock', action='store_true')
    args = parser.parse_args()
    root = args.run.resolve()
    fixture = read_json(root / 'fixture-summary.json')
    harness = read_json(root / 'navigation-reset-summary.json')
    qualifying_start = None
    intervals = []
    previous_time = None
    for sample in fixture['dockingEvaluations']:
        if previous_time is not None and sample['simulationTime'] - previous_time > .25:
            qualifying_start = None
        previous_time = sample['simulationTime']
        if qualified(sample) and (not args.first_dock or inside_first_slip(sample)):
            if qualifying_start is None:
                qualifying_start = sample['simulationTime']
            duration = sample['simulationTime'] - qualifying_start
            if duration >= 5 and sample.get('success'):
                intervals.append({'firstSimulationTime': qualifying_start,
                                  'verifiedSimulationTime': sample['simulationTime'],
                                  'durationSeconds': duration, 'sample': sample})
        else:
            qualifying_start = None
    checks = {
        'nav2Succeeded': fixture['status'] == 'succeeded',
        'independentFiveSecondDocking': bool(intervals),
        'strictHarnessValid': harness['valid'] is True,
        'receivedPlan': len(fixture.get('planHistory', [])) > 0,
        'receivedOdometry': fixture['odometryMessages'] > 0,
        'receivedCostmap': fixture['costmapMessages'] > 0,
        'forwardCommands': fixture['maximumLinearCommand'] > 0,
        'measuredLongRangeMotion': fixture['displacementMeters'] > (10 if args.first_dock else 20),
        'noProhibitedContacts': fixture['maximumProhibitedContactCount'] == 0,
    }
    images = []
    if args.images:
        for name in (('first-dock', 'mid', 'final') if args.first_dock else ('start', 'mid', 'final')):
            path = root / f'{name}.png'
            if not path.exists() or not path.with_suffix('.png.evidence.json').exists():
                images.append({'path': str(path), 'checks': {'captureExists': False}})
                continue
            metadata = json.loads(path.with_suffix('.png.evidence.json').read_text())
            data = base64.b64decode(metadata['costmapDataBase64'])
            image_checks = {
                'pngSignature': path.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n',
                'planAndOdomReceived': metadata['planMessages'] > 0 and metadata['odomMessages'] > 0,
                'receivedLocalCostmap': metadata['costmapMessages'] > 0 and metadata['costmapTopic'] == '/local_costmap/costmap',
                'gridDataRetained': len(data) == metadata['costmapWidth'] * metadata['costmapHeight'],
                'visibleTiles': metadata['renderedCells'] > 0,
                'noVisualColliders': metadata['activeVisualColliders'] == 0,
                'excludedFromSensorCameras': metadata['sensorCamerasExcludeOverlay'] is True,
                'nineWaterProbes': metadata['validWaterHeightProbes'] == 9,
                'raisedAboveSampledWater': metadata['displayedHeightOffset'] - metadata['sampledMaximumWaterHeight'] >= .44,
            }
            if name == 'first-dock':
                image_checks['nearFirstDock'] = metadata['firstDockDistance'] <= 1.61 and metadata['firstDockDistance'] < metadata['secondDockDistance']
            dock_sample = json.loads(metadata.get('dockingEvaluationJson') or '{}')
            if name == 'final':
                image_checks['capturedWhileDockQualified'] = (not args.first_dock or inside_first_slip(dock_sample)) and qualified(dock_sample) and dock_sample.get('success') is True and dock_sample.get('continuousQualifiedSeconds', 0) >= 5
            images.append({'path': str(path), 'sha256': sha(path), 'checks': image_checks,
                           'utc': metadata['utc'], 'odomStamp': metadata['odomStamp'],
                           'planStamp': metadata['planStamp'], 'costmapStamp': metadata['costmapStamp'],
                           'renderedCells': metadata['renderedCells'],
                           'waterHeight': metadata['sampledMaximumWaterHeight'],
                           'displayedHeightOffset': metadata['displayedHeightOffset']})
        checks['captureMetadataVerified'] = all(all(item['checks'].values()) for item in images)
    report = {'schema': 'crane-nav2-visualization-self-verification-v1',
              'run': str(root), 'checks': checks, 'passed': all(checks.values()),
              'firstVerifiedDockingInterval': intervals[0] if intervals else None,
              'actualFirstSlipRequired': args.first_dock, 'finalDockingEvaluation': fixture['dockingEvaluation'], 'images': images,
              'boundary': 'A five-second docking interval does not establish indefinite station keeping. Pixel inspection is recorded separately.'}
    (root / 'self-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'checks': checks}, indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
