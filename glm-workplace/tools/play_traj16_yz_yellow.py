"""Replay the verified Y/Z candidate plan in RoboDK simulation, retaining native yellow line trace."""
from pathlib import Path
import json,hashlib,io,sys,time
from robodk.robolink import *
from robodk.robomath import Pose_2_Fanuc
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',line_buffering=True)
root=Path(__file__).resolve().parents[1]
report_path=root/'sim_scripts/rdk_station_dump/traj16_yz_numeric_20261103_165218/result.json'
report=json.loads(report_path.read_text(encoding='utf-8'));assert report['result']=='PASS'
assert hashlib.sha256(Path(report['file']).read_bytes()).hexdigest()==report['trajectory_sha256']
r=Robolink(port=20500);station=next(s for s in r.getOpenStations() if s.Name()==report['station']);r.setActiveStation(station)
b=r.Item(report['robot'],ITEM_TYPE_ROBOT);assert b.Valid()
assert max(abs(x-y) for x,y in zip(Pose_2_Fanuc(b.PoseTool()),report['tool']))<1e-6
assert max(abs(x-y) for x,y in zip(Pose_2_Fanuc(b.PoseFrame()),report['frame']))<1e-6
for obj in report['objects']:
 item=r.Item(obj['name']);assert item.Valid() and item.Visible()==obj['visible']
 assert max(abs(x-y) for x,y in zip(Pose_2_Fanuc(item.Pose()),obj['pose']))<1e-6,obj['name']
macro=r.Item('TCP真实运动_P2P版',ITEM_TYPE_PROGRAM_PYTHON);copy=report_path.parent/'playback_source_check.py';macro.Save(str(copy));assert hashlib.sha256(copy.read_bytes()).hexdigest()==report['source_sha256']
r.setRunMode(RUNMODE_SIMULATE);r.ShowRoboDK();r.Command('Trace','Off');b.setJoints(report['start_joints']);r.Command('Trace','Reset');r.Command('TriggerAction','actionTraceLine');r.Command('Trace','On');r.Render(True)
b.setSpeed(50,30);r.setSimulationSpeed(2);started=time.monotonic();completed=0
try:
 for i,step in enumerate(report['plan'],1):
  assert r.RunMode()==RUNMODE_SIMULATE and r.ActiveStation().item==station.item
  r.Command('SilentMessage',f'轨迹16 Y/Z微调仿真：P{i}/23')
  for q in step.get('rewinds') or []:
   assert r.RunMode()==RUNMODE_SIMULATE;b.MoveJ(q)
  ways=step.get('waypoints') or []
  if ways:
   for q in ways:
    assert r.RunMode()==RUNMODE_SIMULATE;b.MoveJ(q)
   if max(abs(a-c) for a,c in zip(b.Joints().list()[:6],step['joints']))>1e-4:b.MoveJ(step['joints'])
  else:
   assert r.RunMode()==RUNMODE_SIMULATE;getattr(b,step['method'])(step['joints'])
  completed=i;print('P',i,'/23',step['method'],flush=True)
finally:
 r.Render(True)
 receipt=dict(completed=completed,total=23,seconds=time.monotonic()-started,runmode=r.RunMode(),station=station.Name(),final_joints=b.Joints().list(),trajectory_sha256=report['trajectory_sha256'],trace_style='native line',trace_retained=True)
 (report_path.parent/'playback_result.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
 if completed==23:
  r.Command('SilentMessage','轨迹16 Y/Z微调仿真完成：23/23；黄色轨迹已保留')
  r.Command('Snapshot',str((report_path.parent/'playback_yellow_trace.png').resolve()))
 print(json.dumps(receipt,ensure_ascii=False),flush=True)
