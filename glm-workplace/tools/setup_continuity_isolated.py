from pathlib import Path
import json,struct,io,sys,hashlib
from robodk.robolink import *
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',line_buffering=True)
p=Path('sim_scripts/rdk_station_dump/traj16_continuity_20261103');p.mkdir(exist_ok=True)
r=Robolink(port=20500);b=r.Item('Dobot CR5',ITEM_TYPE_ROBOT);saved=dict(mode=r.RunMode(),joints=b.Joints().list(),base=b.PoseAbs().rows,frame=b.PoseFrame().rows,tool=b.PoseTool().rows,items=[])
for name in ['门把手_bs1','安装台_650x650x80mm','地面_禁止穿越','磨砂圆柱_R150_H50','挡板_半封闭3面']:
 obj=r.Item(name);pts,_=obj.GetPoints(FEATURE_OBJECT_MESH);file=p/(name+'.stl');buf=bytearray(b'offline mesh copy'.ljust(80,b' '))+struct.pack('<I',len(pts)//3)
 for i in range(0,len(pts),3):buf+=struct.pack('<12fH',0,0,0,*[float(x) for row in pts[i:i+3] for x in row[:3]],0)
 file.write_bytes(buf);saved['items'].append(dict(name=name,file=str(file.resolve()),pose=obj.Pose().rows,absolute=obj.PoseAbs().rows,geometry=obj.GeometryPose().rows,is_handle=name=='门把手_bs1'))
r.Item('TCP真实运动_P2P版',ITEM_TYPE_PROGRAM_PYTHON).Save(str((p/'station_p2p.py').resolve()));(p/'live_snapshot.json').write_text(json.dumps(saved,ensure_ascii=False,indent=2),encoding='utf-8')
assert r.RunMode()==saved['mode'] and b.Joints().list()==saved['joints'];print('exported read-only; main mode',saved['mode'])
sim=Robolink(port=20501,args=['-NEWINSTANCE','-NOUI','-NOSPLASH'],robodk_path=r'D:/software/RoboDK/bin/RoboDK.exe');sim.setRunMode(RUNMODE_SIMULATE)
base=sim.AddFrame('本体基座');base.setPose(Mat(saved['base']));model=sim.AddFile(str(Path('sim_scripts/rdk_station_dump/body_alignment_20261103/final_aligned_body.robot').resolve()));model.setName('Dobot CR5_本体与碰撞对齐130');parent=model.Parent();parent.setPose(Mat(saved['base'])*invH(model.PoseAbs())*parent.PoseAbs())
for item in saved['items']:
 obj=sim.AddFile(item['file']);obj.setName(item['name']);obj.setGeometryPose(Mat(item['geometry']))
 if item['is_handle']:obj.setParent(model);obj.setPose(Mat(item['pose']))
 else:obj.setPose(Mat(item['absolute']))
t=model.AddTool(transl(0,0,130),'CR5_TCP_130mm');model.setPoseTool(t);model.setPoseFrame(eye(4));print('isolated ready',sim.PORT,flush=True)
