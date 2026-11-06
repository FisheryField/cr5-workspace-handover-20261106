"""Show the fully checked retreat-adjusted 130mm plan in simulation only."""
import json, hashlib
from pathlib import Path
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL, RUNMODE_SIMULATE
from robodk.robomath import Fanuc_2_Pose
base = Path(__file__).resolve().parents[1]
folder = base/'sim_scripts/rdk_station_dump/traj16_tune130_20261029_151605'
tuning = json.loads((folder/'result.json').read_text(encoding='utf-8'))
receipt = json.loads((folder/'applied.json').read_text(encoding='utf-8'))
baseline = json.loads((base/'sim_scripts/rdk_station_dump/traj16_tcp130_20261029_150821/result.json').read_text(encoding='utf-8'))
candidate, = [c for c in tuning['candidates'] if c['label']=='B_P18_P22']
assert candidate['result']=='PASS'
data = Path(receipt['file']).read_bytes()
assert hashlib.sha256(data).hexdigest()==receipt['sha256']
assert json.loads(data.decode('utf-8-sig'))==candidate['records']
report = dict(baseline, plan=candidate['plan'], tool=[0,0,130,0,0,0], trajectory_sha256=receipt['sha256'])
report_path = folder/'playback_certificate.json'
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
rdk = Robolink(port=20500)
robot = rdk.Item('',ITEM_TYPE_ROBOT)
rdk.setRunMode(RUNMODE_SIMULATE)
name = '_轨迹16仿真_TCP130mm'
tool = rdk.Item(name,ITEM_TYPE_TOOL)
if not tool.Valid():
    tool = robot.AddTool(Fanuc_2_Pose([0,0,130,0,0,0]),name)
assert max(abs(tool.PoseTool()[i,j]-Fanuc_2_Pose([0,0,130,0,0,0])[i,j]) for i in range(4) for j in range(4))<1e-8
robot.setPoseTool(tool)
runner = Path(__file__).with_name('play_traj16_trace.py')
code = runner.read_text(encoding='utf-8')
code = code.replace('rdk.setSimulationSpeed(5)', 'rdk.setSimulationSpeed(2)')
code = code.replace("        points = list(step.get('waypoints') or [])", """        for rewind in step.get('rewinds') or []:
            assert rdk.RunMode() == RUNMODE_SIMULATE
            robot.MoveJ(rewind)
        points = list(step.get('waypoints') or [])""")
import sys
sys.argv = [str(runner),str(report_path)]
exec(compile(code,str(runner),'exec'),dict(__file__=str(runner),__name__='__main__'))
