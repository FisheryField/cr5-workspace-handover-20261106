"""Play the certified trajectory16 plan in simulation and retain TCP trace."""
import io, sys, json, hashlib, time
from pathlib import Path
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_PROGRAM_PYTHON, RUNMODE_SIMULATE, WINDOWSTATE_NORMAL
from robodk.robomath import Pose_2_Fanuc
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
base = Path(__file__).resolve().parents[1]
report_path = base/'sim_scripts'/'rdk_station_dump'/'traj16_precheck_20261027_145923'/'result.json'
if len(sys.argv) > 1:
    report_path = Path(sys.argv[1])
report = json.loads(report_path.read_text(encoding='utf-8'))
assert report['result'] == 'PASS'
assert hashlib.sha256(Path(report['file']).read_bytes()).hexdigest() == report['trajectory_sha256'], 'Trajectory changed after precheck; rerun precheck first'
rdk = Robolink(port=20500)
robot = rdk.Item('', ITEM_TYPE_ROBOT)
assert rdk.ActiveStation().Name() == report['station']
assert max(abs(a-b) for a,b in zip(Pose_2_Fanuc(robot.PoseTool()), report['tool'])) < 1e-6
assert max(abs(a-b) for a,b in zip(Pose_2_Fanuc(robot.PoseFrame()), report['frame'])) < 1e-6
for obj in report['objects']:
    item = rdk.Item(obj['name'])
    assert item.Valid() and item.Visible() == obj['visible'], 'Scene item changed: '+obj['name']
    assert max(abs(a-b) for a,b in zip(Pose_2_Fanuc(item.Pose()), obj['pose'])) < 1e-6, 'Scene pose changed: '+obj['name']
macros = [i for i in rdk.ItemList(ITEM_TYPE_PROGRAM_PYTHON) if i.Name() == 'TCP真实运动_P2P版']
assert len(macros) == 1
macro_copy = report_path.parent/'playback_source_check.py'
macros[0].Save(str(macro_copy))
assert hashlib.sha256(macro_copy.read_bytes()).hexdigest() == report['source_sha256'], 'P2P macro changed'
rdk.setRunMode(RUNMODE_SIMULATE)
rdk.ShowRoboDK()
rdk.setWindowState(WINDOWSTATE_NORMAL)
rdk.Command('Trace', 'Off')
robot.setJoints(report['start_joints'])
rdk.Render(True)
rdk.Command('Trace', 'Reset')
rdk.Command('Trace', 'On')
robot.setSpeed(50, 30)
rdk.setSimulationSpeed(5)
started = time.monotonic()
completed = 0
try:
    for number, step in enumerate(report['plan'], 1):
        assert rdk.RunMode() == RUNMODE_SIMULATE, 'Run mode changed; stopping simulation'
        points = list(step.get('waypoints') or [])
        for q in points:
            assert rdk.RunMode() == RUNMODE_SIMULATE
            robot.MoveJ(q)
        assert rdk.RunMode() == RUNMODE_SIMULATE
        robot.MoveJ(step['joints'])
        completed = number
        print('P%d/%d %s J6=%.2f %s' % (number, len(report['plan']), step['method'], step['joints'][5], step.get('p2p_note','')), flush=True)
    print('SIMULATION COMPLETE %d/%d %.1fs; TCP trace retained; model at endpoint' % (completed, len(report['plan']), time.monotonic()-started))
finally:
    rdk.setRunMode(RUNMODE_SIMULATE)
    rdk.Command('Trace', 'On')
    rdk.Render(True)
    result = dict(completed=completed, total=len(report['plan']), runmode=rdk.RunMode(),
                  final_joints=robot.Joints().list(), tool=Pose_2_Fanuc(robot.PoseTool()),
                  trace='On', trajectory_sha256=report['trajectory_sha256'])
    (report_path.parent/'playback_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('PLAYBACK_RESULT', json.dumps(result, ensure_ascii=False))
