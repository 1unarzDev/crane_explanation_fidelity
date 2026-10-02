"""Development start/goal sampling from first-party map, with geometric clearance."""
import hashlib
import json
import math
from pathlib import Path
import random
import numpy as np
import yaml

MAP = Path('/opt/ros/humble/share/pal_maps/maps/home/map.yaml')

def read_pgm(path):
    with path.open('rb') as stream:
        assert stream.readline().strip() == b'P5'
        tokens = []
        while len(tokens) < 3:
            line = stream.readline()
            if not line.startswith(b'#'):
                tokens.extend(line.split())
        width, height, maximum = map(int, tokens)
        if maximum != 255:
            raise ValueError('unsupported source-map encoding')
        values = np.frombuffer(stream.read(), dtype=np.uint8)
        if len(values) != width * height:
            raise ValueError('source-map size mismatch')
        return values.reshape((height, width))

def sample(seed):
    config = yaml.safe_load(MAP.read_text())
    pgm = MAP.parent / config['image']
    pixels = read_pgm(pgm)
    resolution = config['resolution']
    radius = math.ceil(.6 / resolution)
    candidates = []
    # Conservative square clearance is stronger than a .6 m radial disk.
    for row in range(radius, pixels.shape[0] - radius):
        for col in range(radius, pixels.shape[1] - radius):
            x = config['origin'][0] + (col + .5)*resolution
            y = config['origin'][1] + (pixels.shape[0] - row - .5)*resolution
            if -6 <= x <= 1.2 and -.5 <= y <= 2.0 and np.all(pixels[row-radius:row+radius+1, col-radius:col+radius+1] >= 254):
                candidates.append((x, y))
    if not candidates:
        raise ValueError('empty collision-free frame')
    rng = random.Random(seed)
    start = rng.choice(candidates)
    goals = [g for g in candidates if 3 <= math.dist(g,start) <= 5.5]
    if not goals:
        raise ValueError('no goal in predeclared distance frame')
    goal = rng.choice(goals)
    return {'profile':'home_top_room_clearance_v4_development', 'map_yaml_sha256': hashlib.sha256(MAP.read_bytes()).hexdigest(),
            'map_pgm_sha256': hashlib.sha256(pgm.read_bytes()).hexdigest(), 'start_xy':start,'start_yaw':rng.uniform(-math.pi,math.pi),
            'goal_xy':goal,'goal_yaw':rng.uniform(-math.pi,math.pi),'candidate_start_n':len(candidates),'candidate_goal_n':len(goals),
            'required_clearance_m':.6,'distance_m':math.dist(start,goal), 'sampling_bounds_xy':[-6,1.2,-.5,2.0]}
