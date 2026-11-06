"""Evaluate removing transition anchors P12/P13 without changing work points."""
import io, sys, json, hashlib
from pathlib import Path
from robodk.robolink import RUNMODE_SIMULATE
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
base = Path(__file__).resolve().parents[1]
directory = base/'sim_scripts'/'rdk_station_dump'/'traj16_precheck_20261027_145923'
baseline = json.loads((directory/'result.json').read_text(encoding='utf-8'))
path = Path(baseline['file'])
data = path.read_bytes()
assert hashlib.sha256(data).hexdigest() == baseline['trajectory_sha256'], 'Trajectory changed; review fresh points first'
src = (directory/'station_p2p.py').read_text(encoding='utf-8')
ns = {}
exec(compile(src[:src.index('root = tk.Tk()')], 'planner-head', 'exec'), ns)
rdk, robot = ns['RDK'], ns['robot']
mode, saved = rdk.RunMode(), robot.Joints().list()[:6]
logs = []
def log(message):
    logs.append(str(message))
    print(message, flush=True)
ns['log'] = log
result = {'removed_original_points': [12,13], 'input_sha256': baseline['trajectory_sha256']}
def metrics(plan):
    previous = baseline['start_joints']
    cost = j6 = 0.0
    for step in plan:
        for q in list(step.get('rewinds') or []) + list(step.get('waypoints') or []) + [step['joints']]:
            cost += max(abs(a-b) for a,b in zip(previous,q))
            j6 += abs(q[5]-previous[5])
            previous = q
    return dict(points=len(plan), joint_travel_maxaxis_sum_deg=round(cost,3), j6_travel_deg=round(j6,3))
try:
    assert max(abs(a-b) for a,b in zip(ns['Pose_2_Fanuc'](robot.PoseTool()), baseline['tool'])) < 1e-6
    rdk.setRunMode(RUNMODE_SIMULATE)
    rdk.Command('Trace','Off')
    records = json.loads(data.decode('utf-8-sig'))
    candidate = [rec for idx,rec in enumerate(records,1) if idx not in (12,13)]
    validated = ns['_retreat_orientation_records'](ns['_validated_records'](candidate))
    robot.setJoints(baseline['start_joints'])
    plan = ns['_plan_continuous_trajectory'](validated, 500.0, log)
    result.update(result='PASS', records=candidate, plan=plan, metrics=metrics(plan), baseline_metrics=metrics(baseline['plan']))
    skip = json.loads((directory/'flow_without_P13.json').read_text(encoding='utf-8'))
    result['skip_P13_metrics'] = metrics(skip['plan'])
    for label in ('baseline_metrics','skip_P13_metrics','metrics'):
        print(label, result[label], flush=True)
    for idx in range(10, min(15,len(plan))):
        print('NEW_P%d ORIGINAL_P%d J6=%.3f %s' % (idx+1, idx+3 if idx>=11 else idx+1,plan[idx]['joints'][5],plan[idx].get('p2p_note','')))
except Exception as exc:
    result.update(result='FAIL', error=str(exc))
    print('FAIL', result['error'])
finally:
    robot.setJoints(saved)
    rdk.setRunMode(mode)
    rdk.Render(True)
    rdk.Command('Trace','On')
    result['logs'] = logs
    result['source_unchanged'] = path.read_bytes() == data
    output = directory/'optimization_remove_P12_P13.json'
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('RESULT', result['result'], output, flush=True)
