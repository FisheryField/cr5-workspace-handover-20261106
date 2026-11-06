"""Run only the station P2P planner on trajectory16. Never execute motion."""
import io, sys, json, hashlib, datetime, traceback
from pathlib import Path
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_PROGRAM_PYTHON, RUNMODE_SIMULATE
from robodk.robomath import Pose_2_Fanuc
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
base = Path(__file__).resolve().parents[1]
path = Path(r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹16.json')
out = base / 'sim_scripts' / 'rdk_station_dump' / ('traj16_precheck_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
out.mkdir(parents=True)
rdk = Robolink(port=20500)
robot = rdk.Item('', ITEM_TYPE_ROBOT)
macros = [it for it in rdk.ItemList(ITEM_TYPE_PROGRAM_PYTHON) if it.Name() == 'TCP真实运动_P2P版']
assert len(macros) == 1, 'station P2P macro missing or duplicated'
source = out / 'station_p2p.py'
macros[0].Save(str(source))
code = source.read_text(encoding='utf-8')
lines = code.splitlines()
stop = next(i for i, line in enumerate(lines) if line.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), str(source), 'exec'), ns)
rdk, robot = ns['RDK'], ns['robot']
logs = []
def log(message):
    message = str(message)
    logs.append(message)
    print(message, flush=True)
def forbidden(*args, **kwargs):
    raise RuntimeError('Hardware access forbidden in offline precheck')
ns.update(log=log, _file_log=log, ensure_connected=forbidden, _controller_feedback=forbidden,
          _live_joints=forbidden, _single_move_settle=forbidden)
mode, joints = rdk.RunMode(), robot.Joints().list()[:6]
saved_joints = joints[:]
if '--start-zero' in sys.argv:
    joints = [0.0] * 6
tool, frame = robot.PoseTool(), robot.PoseFrame()
data = path.read_bytes()
report = dict(file=str(path), trajectory_sha256=hashlib.sha256(data).hexdigest(),
              source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              disk_source_matches=source.read_bytes() == (base/'sim_scripts'/'TCP真实运动_P2P版.py').read_bytes(),
              station=rdk.ActiveStation().Name(), version=ns.get('LOG_VERSION'),
              start_joints=joints, tool=Pose_2_Fanuc(tool), frame=Pose_2_Fanuc(frame),
              deviation_mm=500.0,
              objects=[dict(name=it.Name(), pose=Pose_2_Fanuc(it.Pose()), visible=it.Visible())
                       for it in rdk.ItemList() if it.Type() == 5])
print('CONDITIONS', json.dumps(report, ensure_ascii=False), flush=True)
try:
    assert abs(tool[2,3] - 126) < 1e-6, 'Active TCP is not 126mm; do not silently use a different tool'
    records = ns['_validated_records'](json.loads(data.decode('utf-8-sig')))
    report['input_points'] = len(records)
    records = ns['_retreat_orientation_records'](records)
    report['expanded_points'] = len(records)
    print('POINTS', report['input_points'], '->', len(records), flush=True)
    rdk.setRunMode(RUNMODE_SIMULATE)
    rdk.Command('Trace', 'Off')
    robot.setJoints(joints)
    plan = ns['_plan_continuous_trajectory'](records, 500.0, log)
    lower, upper, _ = robot.JointLimits()
    assert all(ns['_real_limit_ok'](step['joints'], lower.list(), upper.list()) for step in plan)
    report.update(result='PASS', planned_points=len(plan), plan=plan)
    for i, step in enumerate(plan, 1):
        print('P%d %s waypoints=%d %s' % (i, step['method'], len(step.get('waypoints') or []), step.get('p2p_note','')))
except Exception as exc:
    report.update(result='FAIL', error=type(exc).__name__ + ': ' + str(exc))
    print('FAIL', report['error'], flush=True)
finally:
    robot.setJoints(saved_joints)
    rdk.setRunMode(mode)
    rdk.Render(True)
    report['restored_joints'] = robot.Joints().list()[:6]
    report['restored_tool'] = Pose_2_Fanuc(robot.PoseTool())
    report['trajectory_unchanged'] = path.read_bytes() == data
    report['logs'] = logs
    (out/'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('RESULT', report['result'], 'REPORT', out/'result.json', flush=True)
