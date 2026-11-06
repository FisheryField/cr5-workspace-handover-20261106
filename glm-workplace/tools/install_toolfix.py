"""Install reviewed TCP fix; only TCP selection and macro source are changed."""
import ast, datetime, hashlib, io, sys
from pathlib import Path
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL, ITEM_TYPE_PROGRAM_PYTHON
from robodk.robomath import eye, Fanuc_2_Pose, Pose_2_Fanuc
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
base = Path(__file__).resolve().parents[1]
source = base / 'sim_scripts' / 'TCP真实运动_P2P版.py'
code = source.read_text(encoding='utf-8')
tree = ast.parse(code)
names = {'_same_tool_pose', '_named_tool', '_restore_tool', '_single_move_settle', '_ensure_canonical_tool'}
module = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[])
rdk = Robolink(port=20500)
robot = rdk.Item('', ITEM_TYPE_ROBOT)
q_before = robot.Joints().list()
geometry = [(it, it.Pose()) for it in rdk.ItemList() if it.Type() == 5]
ns = dict(RDK=rdk, robot=robot, ITEM_TYPE_TOOL=ITEM_TYPE_TOOL, eye=eye, Fanuc_2_Pose=Fanuc_2_Pose,
          CANONICAL_TOOL=(0, 0, 126, 0, 0, 0), TCP_TOOL_NAME='CR5_TCP_126mm',
          FLANGE_TOOL_NAME='_CR5_FLANGE_DIRECT_TEMP', _tool_window_depth=0, log=print)
exec(compile(module, str(source), 'exec'), ns)
ns['_ensure_canonical_tool']()
canonical = robot.getLink(ITEM_TYPE_TOOL)
expected = Fanuc_2_Pose([0, 0, 126, 0, 0, 0])
same = ns['_same_tool_pose']
handle = rdk.Item('门把手_bs1')
for case in ('success', 'exception', 'nested_retry'):
    calls = []
    def core(method, target, required, expected_q, flange, retry):
        # No motion method is ever called. Exercise only the real API tool switch.
        assert same(robot.PoseTool(), eye(4)), 'flange TCP not identity'
        assert same(canonical.PoseTool(), expected), 'canonical TCP definition was mutated'
        assert not handle.Visible()
        calls.append(retry)
        if case == 'exception': raise ValueError('test-only exception')
        if case == 'nested_retry' and retry == 0:
            return ns['_single_move_settle'](method, target, required, expected_q, True, 1)
    ns['_settle_core'] = core
    try: ns['_single_move_settle']('MoveL', eye(4), False, q_before, True)
    except ValueError:
        if case != 'exception': raise
    assert same(robot.PoseTool(), expected)
    assert robot.getLink(ITEM_TYPE_TOOL).item == canonical.item
    assert handle.Visible() and ns['_tool_window_depth'] == 0
    if case == 'nested_retry': assert calls == [0, 1]
    print('LIVE_API_PASS', case, Pose_2_Fanuc(robot.PoseTool()))
assert robot.Joints().list() == q_before
assert all(same(it.Pose(), pose) for it, pose in geometry)
print('PASS model joints and geometry unchanged')

name = 'TCP真实运动_P2P版'
old = [it for it in rdk.ItemList(ITEM_TYPE_PROGRAM_PYTHON) if it.Name() == name]
assert len(old) == 1, 'expected one original macro'
out = base / 'sim_scripts' / 'rdk_station_dump' / ('toolfix_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
out.mkdir(parents=True)
old[0].Save(str(out / 'before.py'))
new = rdk.AddFile(str(source))
try:
    new.Save(str(out / 'installed.py'))
    assert (out / 'installed.py').read_bytes() == source.read_bytes(), 'station source differs'
except BaseException:
    new.Delete()
    raise
old[0].setName(name + '_修复前_v14w40_20261027')
new.setName(name)
assert same(robot.PoseTool(), expected)
print('INSTALLED', name, hashlib.sha256(source.read_bytes()).hexdigest())
print('ACTIVE_TCP', robot.getLink(ITEM_TYPE_TOOL).Name(), Pose_2_Fanuc(robot.PoseTool()))
print('BACKUP', out)
print('No robot connection, EnableRobot, motion, or station save was invoked.')
