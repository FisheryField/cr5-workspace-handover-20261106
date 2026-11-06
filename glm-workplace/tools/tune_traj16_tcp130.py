"""Evaluate retreat-only orientation changes with full offline collision checks."""
import io, sys, json, hashlib, datetime, copy, time
from pathlib import Path
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL, RUNMODE_SIMULATE
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
base = Path(__file__).resolve().parents[1]
baseline = json.loads((base/'sim_scripts/rdk_station_dump/traj16_tcp130_20261029_150821/result.json').read_text(encoding='utf-8'))
path = Path(baseline['file'])
data = path.read_bytes()
assert hashlib.sha256(data).hexdigest() == baseline['trajectory_sha256']
records = json.loads(data.decode('utf-8-sig'))
out = base/'sim_scripts/rdk_station_dump'/('traj16_tune130_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
out.mkdir(parents=True)
rdk = Robolink(port=20500)
macro, = [it for it in rdk.ItemList(ITEM_TYPE_PROGRAM_PYTHON) if it.Name() == 'TCP真实运动_P2P版']
source = out/'station_p2p.py'
macro.Save(str(source))
assert hashlib.sha256(source.read_bytes()).hexdigest() == baseline['source_sha256']
code = source.read_text(encoding='utf-8')
ns = {}
exec(compile(code[:code.index('root = tk.Tk()')], str(source), 'exec'), ns)
rdk, robot = ns['RDK'], ns['robot']
def forbidden(*args, **kwargs):
    raise RuntimeError('Hardware access forbidden')
for name in ('ensure_connected', '_controller_feedback', '_live_joints', '_single_move_settle'):
    ns[name] = forbidden
mode, saved = rdk.RunMode(), robot.Joints().list()[:6]
original_link, original_tool = robot.getLink(ITEM_TYPE_TOOL), robot.PoseTool()
temporary = None
logs = []
def log(message):
    logs.append(str(message))
    print(message, flush=True)
ns.update(log=log, _file_log=log)
def metrics(plan):
    previous = baseline['start_joints']
    cost = j6 = 0.0
    reversals = 0
    direction = 0
    for step in plan:
        for q in list(step.get('rewinds') or []) + list(step.get('waypoints') or []) + [step['joints']]:
            cost += max(abs(a-b) for a,b in zip(previous,q))
            delta = q[5] - previous[5]
            j6 += abs(delta)
            if abs(delta) > 1:
                sign = 1 if delta > 0 else -1
                reversals += int(direction != 0 and sign != direction)
                direction = sign
            previous = q
    return dict(joint_travel_maxaxis_sum_deg=round(cost,3), j6_travel_deg=round(j6,3), j6_direction_reversals=reversals)
report = dict(file=str(path), input_sha256=hashlib.sha256(data).hexdigest(), tested_tool=[0,0,130,0,0,0],
              baseline_metrics=metrics(baseline['plan']), candidates=[])
try:
    # Require the same obstacle positions as the baseline.
    for obj in baseline['objects']:
        item = rdk.Item(obj['name'])
        assert max(abs(a-b) for a,b in zip(Pose_2_Fanuc(item.Pose()), obj['pose'])) < 1e-6
    temporary = robot.AddTool(Fanuc_2_Pose([0,0,130,0,0,0]), '_offline_TCP130_tuning')
    robot.setPoseTool(temporary)
    rdk.setRunMode(RUNMODE_SIMULATE)
    rdk.Command('Trace','Off')
    for label, changes in [('A_P18', {18:19}), ('B_P18_P22', {18:19,22:21})]:
        candidate = copy.deepcopy(records)
        for dest, src in changes.items():
            candidate[dest-1]['values'][3:6] = records[src-1]['values'][3:6]
        assert all(rec == records[i] for i,rec in enumerate(candidate) if i+1 not in changes)
        validated = ns['_retreat_orientation_records'](ns['_validated_records'](candidate))
        robot.setJoints(baseline['start_joints'])
        # An ordering hint, not a cached certificate: every check runs again.
        context = repr((validated, baseline['start_joints'], robot.PoseFrame().rows, robot.PoseTool().rows, 500.0))
        ns['_preferred_seed'] = (context, baseline['plan'][0]['joints'])
        entry = dict(label=label, changed_points=list(changes), records=candidate)
        start = time.perf_counter()
        print('CANDIDATE', label, flush=True)
        try:
            plan = ns['_plan_continuous_trajectory'](validated,500.0,log)
            lower,upper,_ = robot.JointLimits()
            assert all(ns['_real_limit_ok'](s['joints'],lower.list(),upper.list()) for s in plan)
            entry.update(result='PASS',plan=plan,metrics=metrics(plan))
        except ValueError as exc:
            entry.update(result='FAIL',error=str(exc))
        entry['seconds'] = time.perf_counter()-start
        report['candidates'].append(entry)
        (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print('CANDIDATE_RESULT',label,entry['result'],entry.get('metrics'), flush=True)
finally:
    if temporary is not None:
        robot.setPoseTool(original_link if original_link.Valid() else original_tool)
        temporary.Delete()
    robot.setJoints(saved)
    rdk.setRunMode(mode)
    rdk.Render(True)
    rdk.Command('Trace','On')
    report.update(logs=logs, trajectory_unchanged=path.read_bytes()==data, restored_tool=Pose_2_Fanuc(robot.PoseTool()))
    (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('REPORT',out/'result.json',flush=True)
