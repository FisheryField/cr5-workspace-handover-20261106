"""Install the offline-verified macro without starting it or saving the station."""
from pathlib import Path
import ast, datetime, io, sys
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON, ITEM_TYPE_ROBOT
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
base = Path(__file__).resolve().parents[1]
source = base/'sim_scripts/TCP真实运动_P2P版.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
lazy = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_lazy_valid_seeds')
calls = []
ns = dict(_movej_test_cached=lambda start, seed, step: calls.append(seed) or (0 if seed in (2, 3) else 1))
exec(compile(ast.Module(body=[lazy], type_ignores=[]), '<lazy-test>', 'exec'), ns)
iterator = ns['_lazy_valid_seeds']([1, 2, 3], [])
assert next(iterator) == 2 and calls == [1, 2]  # Third seed stays untested.
assert list(iterator) == [3]
assert list(ns['_lazy_valid_seeds']([4, 5], [])) == [4, 5]  # Old all-blocked fallback.
print('PASS lazy ordering and all-blocked fallback')
rdk = Robolink(port=20500)
robot = rdk.Item('', ITEM_TYPE_ROBOT)
before = (robot.Joints().list(), robot.PoseTool().rows, rdk.RunMode())
name = 'TCP真实运动_P2P版'
old, = [it for it in rdk.ItemList(ITEM_TYPE_PROGRAM_PYTHON) if it.Name() == name]
out = base/'sim_scripts/rdk_station_dump'/('precheck_speed_install_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
out.mkdir(parents=True)
old.Save(str(out/'before.py'))
new = rdk.AddFile(str(source))
try:
    new.Save(str(out/'installed.py'))
    assert (out/'installed.py').read_bytes() == source.read_bytes()
    assert before == (robot.Joints().list(), robot.PoseTool().rows, rdk.RunMode())
except BaseException:
    new.Delete()
    raise
old.setName(name+'_优化前_v14w41_20261027')
new.setName(name)
print('INSTALLED', out)
print('No hardware connection, movement, macro execution or station save.')
