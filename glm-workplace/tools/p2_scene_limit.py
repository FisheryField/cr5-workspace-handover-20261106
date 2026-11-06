"""Read the live scene and test Y-3 variants in a separate simulation instance."""
from pathlib import Path
import json, hashlib, datetime, io, sys, struct, copy, traceback
import numpy as np
from robodk.robolink import *
from robodk.robomath import *
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',line_buffering=True)
root=Path(__file__).resolve().parents[1]
out=root/'sim_scripts/rdk_station_dump'/('p2_scene_limit_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
out.mkdir(parents=True)
path=Path(r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹17.json')
data=path.read_bytes(); original=json.loads(data.decode('utf-8-sig'))
main=Robolink(port=20500); body=main.Item('Dobot CR5',ITEM_TYPE_ROBOT)
before=dict(mode=main.RunMode(),joints=body.Joints().list(),tool=body.PoseTool().rows,
    frame=body.PoseFrame().rows,base=body.PoseAbs().rows)
source=out/'station_p2p.py'
macros=[it for it in main.ItemList(ITEM_TYPE_PROGRAM_PYTHON)
    if it.Name() in ('TCP真实运动_P2P版','TCP真实运动_P2P版_16稳定版')]
assert len(macros)==1,[(it.Name(),it.Type()) for it in macros]
macros[0].Save(str(source))
code=(root/'sim_scripts/TCP真实运动_P2P版.py').read_text(encoding='utf-8').split('root = tk.Tk()')[0]
source.write_text(code,encoding='utf-8')
assert 'v15.22-20261104' in code
snapshot=[]
for name in ['门把手_bs1','安装台_650x650x80mm','地面_禁止穿越','磨砂圆柱_R150_H50','挡板_半封闭3面']:
    obj=main.Item(name,ITEM_TYPE_OBJECT)
    assert obj.Valid(),name
    pts,_=obj.GetPoints(FEATURE_OBJECT_MESH)
    file=out/(name+'.stl')
    buf=bytearray(b'offline read-only mesh snapshot'.ljust(80,b' '))+struct.pack('<I',len(pts)//3)
    for i in range(0,len(pts),3):
        buf+=struct.pack('<12fH',0,0,0,*[float(x) for row in pts[i:i+3] for x in row[:3]],0)
    file.write_bytes(buf)
    snapshot.append(dict(name=name,file=str(file),pose=obj.Pose().rows,
        absolute=obj.PoseAbs().rows,geometry=obj.GeometryPose().rows))
sim=Robolink(port=20501)
assert sim.PORT==20501
sim.setRunMode(RUNMODE_SIMULATE)
assert not sim.ItemList(ITEM_TYPE_ROBOT),'Expected an empty isolated instance'
model=sim.AddFile(str(root/'sim_scripts/rdk_station_dump/body_alignment_20261103/final_aligned_body.robot'))
model.setName('Dobot CR5')
parent=model.Parent()
parent.setPose(Mat(before['base'])*invH(model.PoseAbs())*parent.PoseAbs())
for item in snapshot:
    obj=sim.AddFile(item['file']); obj.setName(item['name']); obj.setGeometryPose(Mat(item['geometry']))
    if item['name']=='门把手_bs1':
        obj.setParent(model); obj.setPose(Mat(item['pose']))
    else:
        obj.setPose(Mat(item['absolute']))
tool=model.AddTool(transl(0,0,130),'CR5_TCP_130mm')
model.setPoseTool(tool);model.setPoseFrame(Mat(before['frame']))
for name in ['磨砂圆柱_R150_H50','挡板_半封闭3面']:
    a=invH(body.PoseAbs())*main.Item(name).PoseAbs()
    b=invH(model.PoseAbs())*sim.Item(name).PoseAbs()
    assert np.max(np.abs(np.array(a.rows)-np.array(b.rows)))<1e-4


ns={}
exec(compile(code.replace('RDK = Robolink()','RDK = Robolink(port=20501)'),str(source),'exec'),ns)
report=json.loads((root/'sim_scripts/rdk_station_dump/traj17_v1522_20261104_095649/result.json').read_text(encoding='utf-8'))[-1]
q=report['plan'][1]['joints']
model.setJoints(q);ns['_enable_obstacle_checks']()
objects=[item for item in snapshot if item['name'] in ['磨砂圆柱_R150_H50','挡板_半封闭3面']]
def setshift(d):
 shift=Mat(before['base'])*transl(0,d,0)*invH(Mat(before['base']))
 for item in objects: sim.Item(item['name']).setPose(shift*Mat(item['absolute']))
 model.setJoints(q)
 return sim.Collisions()
assert setshift(0)==0,'P2 already colliding'
low=0.;high=None
for d in range(1,201):
 if setshift(d): high=float(d);low=d-1.;break
assert high is not None,'No contact found within 200mm'
for _ in range(16):
 mid=(low+high)/2
 if setshift(mid):high=mid
 else:low=mid
setshift(high);details=ns['_collision_details']()
# Leave 0.1 mm on the noncollision side for the scene inspection.
chosen=max(0,low-0.1);setshift(chosen)
placement=[dict(name=item['name'],before_absolute=item['absolute'],target_absolute=sim.Item(item['name']).PoseAbs().rows) for item in objects]
result=dict(p2_joints=q,shift_base_y_mm=chosen,first_collision_y_mm=high,collision_details=details,objects=placement,main_before=before)
(out/'limit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True));print(out/'limit.json')
sim.CloseRoboDK()
