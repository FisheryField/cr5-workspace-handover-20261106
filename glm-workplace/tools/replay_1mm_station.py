from pathlib import Path
import json,hashlib,time
from robodk.robolink import *
from robodk.robomath import *
root=Path(r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump')
report=json.loads((root/'recheck_applied_1mm_20261104_104155/result.json').read_text(encoding='utf-8'))[0]
placement=json.loads((root/'clearance1mm_transition_20261104_103447/placement.json').read_text(encoding='utf-8'))
assert report['result']=='PASS' and hashlib.sha256(Path(placement['trajectory']).read_bytes()).hexdigest()==report['original_trajectory_sha256']
r=Robolink(port=20500);robot=r.Item('Dobot CR5',ITEM_TYPE_ROBOT);assert robot.Valid() and not robot.Busy()
for o in placement['objects']:
 cur=r.Item(o['name'],ITEM_TYPE_OBJECT).PoseAbs();target=Mat(o['target_absolute']);assert max(abs(cur[i,j]-target[i,j]) for i in range(4) for j in range(4))<.01
r.setRunMode(RUNMODE_SIMULATE);assert r.RunMode()==RUNMODE_SIMULATE
start=report['start_joints'];robot.setJoints(start);tool=robot.PoseTool();assert abs(tool[2,3]-130)<.001
name='轨迹17_1mm过渡版_仿真25点'
prog=r.Item(name,ITEM_TYPE_PROGRAM);assert prog.Valid();prog.setRunType(PROGRAM_RUN_ON_SIMULATOR)
message, samples, status=prog.InstructionListJoints(mm_step=3,deg_step=2,collision_check=COLLISION_ON)
print('SAMPLE_STATUS',status,message,flush=True)
if status<0 or any(samples[6,i]!=0 for i in range(samples.size(1))):
 r.Render(True)
 raise RuntimeError('Simulation program path check failed')
curve=r.Item('轨迹17_1mm过渡版_TCP路径',ITEM_TYPE_OBJECT);assert curve.Valid()
r.Render(True)
assert r.RunMode()==RUNMODE_SIMULATE
for col in range(samples.size(1)):
 robot.setJoints(samples[:6,col].list())
 time.sleep(.008)
q_end=robot.Joints().list();expected=report['plan'][-1]['joints']
print('END',q_end,'EXPECTED',expected,flush=True)
assert max(abs(x-y) for x,y in zip(q_end,expected))<.1
print('SIM_COMPLETE',len(report['plan']),samples.size(1),flush=True)
