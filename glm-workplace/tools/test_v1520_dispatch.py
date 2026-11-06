"""Exercise the production dispatcher with all movement and connections mocked."""
from pathlib import Path
import json, copy, re, io, sys
from robodk.robolink import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
folder = Path('sim_scripts/rdk_station_dump/install_v1520_20261103')
source = (folder/'TCP真实运动_P2P版.py').read_text(encoding='utf-8')
ns = {}
exec(compile(source.split('root = tk.Tk()')[0].replace('RDK = Robolink()',
    'RDK = Robolink(port=20501)'), 'dispatch_dryrun', 'exec'), ns)
reports = sorted(Path('sim_scripts/rdk_station_dump').glob('traj16_v1520_check_*/result.json'))
report = json.loads(reports[-1].read_text(encoding='utf-8'))
assert report['result'] == 'PASS' and report['version']=='v15.20-20261103'
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
results=[]
try:
    for case in ('normal', 'missing_certificate', 'direct_disabled'):
        plan=copy.deepcopy(report['plan'])
        if case=='missing_certificate': plan[2].pop('direct_movl_certified')
        ns['real_movldirect_var']=Value(case!='direct_disabled')
        state=dict(q=report['start_joints'][:], point=None)
        logs,sends=[],[]
        def log(message):
            logs.append(str(message))
            match=re.match(r'P(\d+)[：:]',str(message))
            if match: state['point']=int(match[1])
        def require(q,*args,**kwargs):
            assert max(abs(a-b) for a,b in zip(q,state['q']))<1e-5
        def settle(method,target,require_joints=True,expect_target=None,**kwargs):
            sends.append(dict(point=state['point'],method=method,
                flange_space=bool(kwargs.get('flange_space')),direct=expect_target is not None))
            state['q']=list(expect_target if expect_target is not None else target)
            robot.setJoints(state['q'])
        ns.update(log=log,_live_joints=lambda:state['q'][:],
            _controller_feedback=lambda:(state['q'][:],[0]*6,5),
            _require_joints=require,_single_move_settle=settle,
            _move_with_completion_check=lambda method,target,*a,**k:settle(method,target),
            _wait_controller_static=lambda *a,**k:(state['q'][:],True),
            _prepare_real_plan=lambda *a,**k:copy.deepcopy(plan))
        robot.setJoints(state['q'])
        ns['_execute_checked_real'](data)
        if case=='normal':
            assert any('实机执行完成：23/23' in l for l in logs),logs[-10:]
            strokes={n:[s for s in sends if s['point']==n] for n in range(1,24)}
            for n,step in enumerate(plan,1):
                assert len(strokes[n])==1,(n,strokes[n])
                assert strokes[n][0]['method']==step['method'],(n,strokes[n])
            assert strokes[2][0]['method']=='MoveJ'
        else:
            assert not sends,(case,sends)
            assert any('禁止退回' in l for l in logs),logs[-10:]
        results.append(dict(case=case,result='PASS',sends=sends,logs=logs,hardware_access=False))
        print('PASS',case,'commands',len(sends))
finally:
    robot.setJoints(saved)
(folder/'dispatch_dryrun.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
