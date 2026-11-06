"""Dry-run execution dispatcher; no robot movement or controller connections."""
from pathlib import Path
import json, copy, re, io, sys
from robodk.robolink import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
folder = Path('sim_scripts/rdk_station_dump/install_v1519_20261103')
source = (folder/'TCP真实运动_P2P版.py').read_text(encoding='utf-8')
ns = {}
exec(compile(source.split('root = tk.Tk()')[0].replace('RDK = Robolink()',
    'RDK = Robolink(port=20501)'), 'dispatch_dryrun', 'exec'), ns)
report = json.loads(Path('sim_scripts/rdk_station_dump/traj16_v1518_check_20261103_174447/result.json').read_text(encoding='utf-8'))
assert report['version'] == 'v15.19-20261103' and report['result'] == 'PASS'
data = json.loads(Path(report['file']).read_text(encoding='utf-8'))
robot, rdk = ns['robot'], ns['RDK']
saved = robot.Joints().list()
assert rdk.RunMode() == RUNMODE_SIMULATE

class Value:
    def __init__(self, value): self.value = value
    def get(self): return self.value

class Keepalive:
    def Item(self, *args): return self
    def ConnectedState(self): return (0, 'Ready')
    def Connect(self): raise AssertionError('Connection forbidden')

def forbidden(*args, **kwargs): raise AssertionError('Motion forbidden in dry-run')
robot.MoveJ = robot.MoveL = forbidden
ns.update(Robolink=lambda: Keepalive(), real_deviation_var=Value(500),
    real_movldirect_var=Value(True), _movl_direct_ready=lambda: True,
    ensure_connected=lambda: True, _file_log=lambda *a: None)
results = []
try:
    for enabled in (True, False):
        plan = copy.deepcopy(report['plan'])
        if not enabled:
            for step in plan:
                step.pop('direct_movl_certified', None)
                step.pop('direct_send_joints', None)
        state = dict(q=report['start_joints'][:], point=None)
        logs, sends = [], []
        def log(message):
            logs.append(str(message))
            match = re.match(r'P(\d+)[：:]', str(message))
            if match: state['point'] = int(match[1])
        def require(q, *args, **kwargs):
            assert max(abs(a-b) for a,b in zip(q,state['q'])) < 1e-5
        def settle(method, target, require_joints=True, expect_target=None, **kwargs):
            sends.append(dict(point=state['point'], method=method,
                flange_space=bool(kwargs.get('flange_space')), direct=expect_target is not None))
            state['q'] = list(expect_target if expect_target is not None else target)
            robot.setJoints(state['q'])
        def move(method, target, *args, **kwargs): settle(method, target)
        ns.update(log=log, _live_joints=lambda: state['q'][:],
            _controller_feedback=lambda: (state['q'][:], [0]*6, 5),
            _require_joints=require, _single_move_settle=settle,
            _move_with_completion_check=move,
            _wait_controller_static=lambda *a, **k: (state['q'][:], True),
            _prepare_real_plan=lambda *a, **k: copy.deepcopy(plan))
        robot.setJoints(state['q'])
        ns['_execute_checked_real'](data)
        assert any('实机执行完成：23/23' in line for line in logs), logs[-12:]
        strokes = {n: [s for s in sends if s['point'] == n] for n in (9,11)}
        for number, sent in strokes.items():
            if enabled:
                assert len(sent)==1 and sent[0]['method']=='MoveL' and sent[0]['flange_space'], sent
            else:
                assert len(sent)==len(plan[number-1]['waypoints']) and all(s['method']=='MoveJ' for s in sent), sent
        result = dict(certificates_enabled=enabled, strokes=strokes, completed=23,
            hardware_access=False, logs=logs)
        results.append(result)
        print('PASS certificates=',enabled,'dispatch counts=',{n:len(v) for n,v in strokes.items()})
finally:
    robot.setJoints(saved)
(folder/'dispatch_dryrun.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
