"""Hash-guarded development world adaptation: zero-time reset preserving map-compatible saved poses."""
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

p = Path('/ws/src/pal_gazebo_worlds/worlds/home.world')
expected = '6a8cb85937ced0ad178410ec8a946e6a107c2c690c1b93ce9ecfa4ea529d0ee3'
if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
    raise SystemExit('Refusing to adapt unknown/already changed source world')
tree = ET.parse(p)
world = tree.getroot().find('world')
for state in world.findall('state'):
    # Saved furniture poses differ materially from model-definition poses. Preserve
    # those physical states so the published first-party map still matches the world.
    for name in ('sim_time', 'real_time', 'wall_time'):
        element = state.find(name)
        if element is not None:
            element.text = '0 0'
    iterations = state.find('iterations')
    if iterations is not None:
        iterations.text = '0'
plugin = ET.SubElement(world, 'plugin', name='hexar_entity_state_api', filename='libgazebo_ros_state.so')
ET.SubElement(plugin, 'update_rate').text = '20.0'
tree.write(p, encoding='utf-8', xml_declaration=True)
print('adapted_world_sha256', hashlib.sha256(p.read_bytes()).hexdigest())
