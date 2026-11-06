"""Read the live scene and test Y-3 variants in a separate simulation instance."""
from pathlib import Path
import json, hashlib, datetime, io, sys, struct, copy, traceback
import numpy as np
from robodk.robolink import *
from robodk.robomath import *
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',line_buffering=True)
root=Path(__file__).resolve().parents[1]
out=root/'sim_scripts/rdk_station_dump'/('contact_search_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
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

def forbidden(*a,**k): raise AssertionError('Hardware access forbidden in this test')
reports=[]
# Find each exact mesh contact boundary using only the isolated tool/cylinder pair.
handle=sim.Item('门把手_bs1');wheel=sim.Item('磨砂圆柱_R150_H50')
handle_pose=handle.Pose();handle.setParent(sim.ActiveStation())
base_pose=Mat(before['base'])
wheel_base=invH(base_pose)*wheel.PoseAbs()
cz=wheel_base[2,3]
sim.setCollisionActive(COLLISION_OFF);sim.setCollisionActivePair(COLLISION_ON,handle,wheel)
def contact_y(rec,z):
 def hits(y):
  vals=rec['values'][:];vals[1]=y;vals[2]=z
  handle.setPoseAbs(base_pose*Fanuc_2_Pose(vals)*invH(transl(0,0,130))*handle_pose)
  return sim.Collision(handle,wheel)>0
 start=wheel_base[1,3]+200
 prev=start
 for k in range(1,241):
  y=start-k
  if hits(y):
   low=y;high=prev;break
  prev=y
 else: raise ValueError('No radial contact for X='+str(rec['values'][0]))
 for _ in range(18):
  mid=(low+high)/2
  if hits(mid):low=mid
  else:high=mid
 return high
geometric=copy.deepcopy(original);boundaries={}
for i in [2,3,5,8,9,11,13,15,17,19,22]:
 y=contact_y(geometric[i-1],cz);boundaries[i]=y
 geometric[i-1]['values'][1]=y+0.002
 geometric[i-1]['values'][2]=cz
 print('CONTACT',i,y,flush=True)
# Rotation starts at the preceding endpoint; retreat stations keep their offsets.
for i,j in [(4,3),(10,9)]: geometric[i-1]['values'][1:3]=geometric[j-1]['values'][1:3]
for i,j in [(6,5),(7,5),(12,13),(14,15),(16,17),(18,19),(20,19),(21,22)]:
 geometric[i-1]['values'][1]=geometric[j-1]['values'][1]+35
 geometric[i-1]['values'][2]=cz
handle.setParent(model);handle.setPose(handle_pose)
(out/'contact_boundaries.json').write_text(json.dumps(boundaries,indent=2),encoding='utf-8')
try:
 for dy,dz in [(0,0),(40,0),(80,0),(120,0),(40,40),(80,40),(40,-40),(80,-40)]:
  case='dy%d_dz%d'%(dy,dz);candidate=copy.deepcopy(geometric)
  for rec in candidate[1:22]:rec['values'][1]+=dy;rec['values'][2]+=dz
  shift=base_pose*transl(0,dy,dz)*invH(base_pose)
  for item in snapshot:
   if item['name'] in ['磨砂圆柱_R150_H50','挡板_半封闭3面']:sim.Item(item['name']).setPose(shift*Mat(item['absolute']))
  file=out/(case+'.json');file.write_text(json.dumps(candidate,ensure_ascii=False,indent=2),encoding='utf-8')
  ns={};exec(compile(code.replace('RDK = Robolink()','RDK = Robolink(port=20501)'),str(source),'exec'),ns)
  ns.update(ensure_connected=forbidden,_controller_feedback=forbidden,_live_joints=forbidden,_single_move_settle=forbidden)
  logs=[]
  def log(t):logs.append(str(t));print(case,t,flush=True)
  ns.update(log=log,_file_log=log)
  model.setJoints([0]*6)
  records=ns['_retreat_orientation_records'](ns['_validated_records'](candidate))
  result=dict(case=case,dy=dy,dz=dz,candidate_file=str(file),contact_numerical_clearance_mm=.002,contact_boundaries=boundaries)
  try:
   plan=ns['_plan_continuous_trajectory'](records,500.,log);ns['_assert_continuous_dispatch'](records,[0]*6,plan,True)
   result.update(result='PASS',plan=plan)
  except Exception as exc:result.update(result='FAIL',error=str(exc))
  result['logs']=logs;reports.append(result)
  (out/'result.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
  print('RESULT',case,result['result'],result.get('error',''),flush=True)
  if result['result']=='PASS':break
finally:
 assert path.read_bytes()==data
 print('REPORT',out/'result.json',flush=True)
 sim.CloseRoboDK()
