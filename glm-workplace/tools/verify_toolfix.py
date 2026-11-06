"""Exercise tool-window failure paths without sending robot motion commands."""
import ast
from pathlib import Path
from robodk.robolink import ITEM_TYPE_TOOL
from robodk.robomath import eye, transl, Fanuc_2_Pose

source = Path(__file__).resolve().parents[1] / 'sim_scripts' / 'TCP真实运动_P2P版.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
names = {'_same_tool_pose', '_named_tool', '_restore_tool', '_single_move_settle', '_ensure_canonical_tool'}
module = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[])

class Tool:
    def __init__(self, name, pose): self.name, self.pose = name, pose
    def Valid(self): return True
    def Name(self): return self.name
    def Type(self): return ITEM_TYPE_TOOL
    def PoseTool(self): return self.pose

class Handle:
    visible = True
    def Valid(self): return True
    def Visible(self): return self.visible
    def setVisible(self, value): self.visible = value

class Robot:
    def __init__(self):
        self.tools = [Tool('CR5_TCP_126mm', transl(0, 0, 126))]
        self.active = self.tools[0]
        self.fail_restore = 0
    def Childs(self): return self.tools
    def AddTool(self, pose, name):
        item = Tool(name, pose)
        self.tools.append(item)
        return item
    def PoseTool(self): return self.active.pose
    def getLink(self, kind): return self.active
    def setPoseTool(self, value):
        pose = value.pose if isinstance(value, Tool) else value
        if pose[2, 3] and self.fail_restore:
            self.fail_restore -= 1
            raise RuntimeError('injected restore failure')
        self.active = value if isinstance(value, Tool) else Tool('matrix', value)

def namespace(robot, handle):
    ns = dict(robot=robot, RDK=type('RDK', (), {'Item': lambda self, name: handle})(),
              ITEM_TYPE_TOOL=ITEM_TYPE_TOOL, eye=eye, Fanuc_2_Pose=Fanuc_2_Pose,
              CANONICAL_TOOL=(0, 0, 126, 0, 0, 0), TCP_TOOL_NAME='CR5_TCP_126mm',
              FLANGE_TOOL_NAME='_CR5_FLANGE_DIRECT_TEMP', _tool_window_depth=0, log=lambda s: None)
    exec(compile(module, str(source), 'exec'), ns)
    return ns

for case in ('normal', 'motion_error', 'retry', 'restore_once', 'restore_twice', 'custom_tool'):
    robot, handle = Robot(), Handle()
    if case == 'custom_tool': robot.active = Tool('custom', transl(1, 2, 140))
    original, pose = robot.active, robot.PoseTool()
    ns = namespace(robot, handle)
    calls = []
    def core(method, target, required, expected, flange, retry):
        assert ns['_same_tool_pose'](robot.PoseTool(), eye(4))
        assert not handle.visible
        assert ns['_ensure_canonical_tool']() is False
        calls.append(retry)
        if case == 'motion_error': raise ValueError('injected movement failure')
        if case == 'retry' and retry == 0:
            return ns['_single_move_settle'](method, target, required, expected, True, 1)
        if case.startswith('restore_'): robot.fail_restore = 1 if case.endswith('once') else 2
        return 'done'
    ns['_settle_core'] = core
    error = None
    try: ns['_single_move_settle']('MoveL', eye(4), False, [0]*6, True)
    except Exception as exc: error = exc
    assert ns['_tool_window_depth'] == 0 and handle.visible
    if case == 'restore_twice': assert isinstance(error, RuntimeError)
    else:
        assert robot.active is original and ns['_same_tool_pose'](robot.PoseTool(), pose)
        assert isinstance(error, ValueError) if case == 'motion_error' else error is None
    if case == 'retry': assert calls == [0, 1]
    print('PASS', case)
print('PASS source parses; no robot motion invoked')
