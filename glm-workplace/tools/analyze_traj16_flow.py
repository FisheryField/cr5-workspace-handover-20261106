"""Compare transition planning with P13 omitted in memory; do not edit trajectory."""
import sys, io, json, hashlib
from pathlib import Path
from robodk.robolink import Robolink, RUNMODE_SIMULATE, ITEM_TYPE_ROBOT
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
base = Path(__file__).resolve().parents[1]
oldpath = base/'sim_scripts'/'rdk_station_dump'/'traj16_precheck_20261027_145923'/'result.json'
baseline = json.loads(oldpath.read_text(encoding='utf-8'))
data = Path(baseline['file']).read_bytes()
assert hashlib.sha256(data).hexdigest() == baseline['trajectory_sha256']
src = (oldpath.parent/'station_p2p.py').read_text(encoding='utf-8')
head = src[:src.index('root = tk.Tk()')]
ns = {}
exec(compile(head, 'p2p-analysis-head', 'exec'), ns)
rdk, robot = ns['RDK'], ns['robot']
mode, saved = rdk.RunMode(), robot.Joints().list()[:6]
logs = []
def log(message):
    logs.append(str(message))
    print(message, flush=True)
ns['log'] = log
result = {'omitted_original_point': 13, 'trajectory_sha256': baseline['trajectory_sha256']}
try:
    rdk.setRunMode(RUNMODE_SIMULATE)
    print('DIRECT_ORIGINAL_P12_TO_P14_COLLISION_CODE', robot.MoveJ_Test(baseline['plan'][11]['joints'], baseline['plan'][13]['joints'], minstep_deg=1), flush=True)
    records = ns['_validated_records'](json.loads(data.decode('utf-8-sig')))
    records.pop(12)
    records = ns['_retreat_orientation_records'](records)
    robot.setJoints(baseline['start_joints'])
    plan = ns['_plan_continuous_trajectory'](records, 500.0, log)
    result.update(result='PASS', plan=plan, points=len(plan))
    for i in range(10, min(15, len(plan))):
        original = i+1 if i < 12 else i+2
        prev = baseline['start_joints'] if i == 0 else plan[i-1]['joints']
        print('ORIGINAL_P%d J6=%.3f MAX_DELTA=%.3f %s' % (original, plan[i]['joints'][5], max(abs(a-b) for a,b in zip(prev, plan[i]['joints'])), plan[i].get('p2p_note','')))
except Exception as exc:
    result.update(result='FAIL', error=str(exc))
    print('FAIL', str(exc))
finally:
    robot.setJoints(saved)
    rdk.setRunMode(mode)
    rdk.Render(True)
    result['logs'] = logs
    result['trajectory_unchanged'] = Path(baseline['file']).read_bytes() == data
    dest = oldpath.parent/'flow_without_P13.json'
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('RESULT', result['result'], dest)
