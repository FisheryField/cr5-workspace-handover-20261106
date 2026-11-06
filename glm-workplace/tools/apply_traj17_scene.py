from pathlib import Path
import json,datetime,hashlib
from robodk.robolink import *
from robodk.robomath import *
root=Path(r'D:\mydata\glm-workplace')
base=root/'sim_scripts/rdk_station_dump/traj17_search_20261104_094436'
p=json.loads((base/'placement.json').read_text(encoding='utf-8'))
s=json.loads((base/'scene_snapshot.json').read_text(encoding='utf-8'))
r=Robolink(port=20500); robot=r.Item('Dobot CR5',ITEM_TYPE_ROBOT)
assert robot.Valid()
assert not robot.Busy(), 'Robot busy'
def delta(a,b): return max(abs(a[i,j]-b[i,j]) for i in range(4) for j in range(4))
assert delta(robot.PoseAbs(),Mat(s['before']['base']))<1e-5, 'Robot base changed'
assert delta(robot.PoseTool(),Mat(s['before']['tool']))<1e-5, 'TCP changed'
assert delta(robot.PoseFrame(),Mat(s['before']['frame']))<1e-5, 'Reference changed'
out=root/'sim_scripts/rdk_station_dump'/('traj17_main_install_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));out.mkdir()
macros=[it for it in r.ItemList(ITEM_TYPE_PROGRAM_PYTHON) if it.Name() in ('TCP真实运动_P2P版','TCP真实运动_P2P版_16稳定版')]
assert len(macros)==1
macros[0].Save(str(out/'station_script.py'))
assert (out/'station_script.py').read_bytes()==(base/'station_p2p.py').read_bytes(), 'Station script changed'
trajectory=Path(p['trajectory']); candidate=base/'dy20_dz0.json'
assert trajectory.read_bytes()==candidate.read_bytes(), 'Trajectory17 changed'
items=[]
for o in p['objects']:
 it=r.Item(o['name'],ITEM_TYPE_OBJECT);assert it.Valid()
 current=it.PoseAbs(); target=Mat(o['target_absolute'])
 assert min(delta(current,Mat(o['original_absolute'])),delta(current,target))<0.01, 'Object moved externally: '+o['name']
 items.append((it,current,target))
joints=robot.Joints().list();mode=r.RunMode()
(out/'before.json').write_text(json.dumps(dict(joints=joints,mode=mode,objects=[dict(name=it.Name(),pose_absolute=pose.rows) for it,pose,_ in items]),ensure_ascii=False,indent=2),encoding='utf-8')
try:
 for it,_,target in items: it.setPoseAbs(target)
 for it,_,target in items:
  err=delta(it.PoseAbs(),target)
  print('READBACK',it.Name(),err,flush=True)
  assert err<0.01, 'Readback exceeds 0.01mm tolerance'
 assert robot.Joints().list()==joints and r.RunMode()==mode
except:
 for it,pose,_ in items: it.setPoseAbs(pose)
 raise
receipt=dict(station=r.ActiveStation().Name(),objects=[dict(name=it.Name(),pose_absolute=it.PoseAbs().rows,robot_base_pose=Pose_2_Fanuc(invH(robot.PoseAbs())*it.PoseAbs())) for it,_,_ in items],trajectory=str(trajectory),trajectory_sha256=hashlib.sha256(trajectory.read_bytes()).hexdigest(),tcp=Pose_2_Fanuc(robot.PoseTool()),joints_unchanged=True,mode_unchanged=True,hardware_motion_sent=False,station_file_saved=False,script_unchanged=True)
(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=True));print(str(out/'receipt.json'))

