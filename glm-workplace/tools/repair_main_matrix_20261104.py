from pathlib import Path
import json,datetime,hashlib,traceback
import numpy as np
from robodk.robolink import *
from robodk.robomath import *
root=Path(r'D:\mydata\glm-workplace');out=root/'sim_scripts/rdk_station_dump'/('main_matrix_repair_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));out.mkdir()
formal=root/'sim_scripts/TCP真实运动_P2P版.py';code=formal.read_text(encoding='utf-8-sig').split('root = tk.Tk()')[0];ns={};exec(compile(code,str(formal),'exec'),ns)
r=ns['RDK'];b=ns['robot'];assert r.PORT==20500 and b.Valid() and not b.Busy()
start,v,m=ns['_controller_feedback']();assert m==5 and max(map(abs,v))<.1
traj=Path(r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹17.json');data=traj.read_bytes();assert hashlib.sha256(data).hexdigest()=='549d6fa7998ed8dc76a008df93f4078f5112887eefa1b1e57fadb1c9f5a40c55'
objects=[r.Item(n,ITEM_TYPE_OBJECT) for n in ['安装台_650x650x80mm','地面_禁止穿越','磨砂圆柱_R150_H50','挡板_半封闭3面']];assert all(i.Valid() for i in objects)
scene=objects[0].Parent();assert all(i.Parent().item==scene.item for i in objects)
items=[scene,b.Parent()]+objects;before=[i.Pose() for i in items];world=[i.PoseAbs() for i in items]
(out/'before.json').write_text(json.dumps([dict(name=i.Name(),pose=m.rows,absolute=w.rows) for i,m,w in zip(items,before,world)],ensure_ascii=False,indent=2),encoding='utf8')
def normalize(p):
 a=np.array(p.rows);rot=a[:3,:3];u,sv,vt=np.linalg.svd(rot);assert np.max(abs(sv-1))<.001 and np.linalg.det(rot)>0
 a[:3,:3]=u@vt;return Mat(a.tolist())
new=[normalize(m) for m in before];r.setRunMode(RUNMODE_SIMULATE);assert r.RunMode()==RUNMODE_SIMULATE
try:
 for it,pose in zip(items,new):it.setPose(pose)
 for it,w in zip(items,world):
  p=it.PoseAbs();assert p.isHomogeneous(),it.Name();assert max(abs(x-y) for x,y in zip(p.Pos(),w.Pos()))<.02,it.Name()
except:
 for it,pose in zip(items,before):it.setPose(pose)
 raise
print('MATRICES_REPAIRED',flush=True)
saved=b.Joints().list();b.setJoints(start)
logs=[]
def log(t):logs.append(str(t));print(t,flush=True)
def forbidden(*a,**k):raise RuntimeError('Hardware access disabled during precheck')
ns.update(log=log,_file_log=log,ensure_connected=forbidden,_controller_feedback=forbidden,_live_joints=forbidden,_single_move_settle=forbidden)
result=dict(version=ns['LOG_VERSION'],trajectory=str(traj),controller_start=start,matrices=[dict(name=i.Name(),absolute=i.PoseAbs().rows,homogeneous=i.PoseAbs().isHomogeneous()) for i in items])
try:
 records=ns['_retreat_orientation_records'](ns['_validated_records'](json.loads(data.decode('utf-8-sig'))));plan=ns['_plan_continuous_trajectory'](records,500.,log);ns['_assert_continuous_dispatch'](records,start,plan,True)
 result.update(result='PASS',points=len(plan),certified_movl=[i for i,s in enumerate(plan,1) if s.get('direct_movl_certified')])
except Exception as e:
 result.update(result='FAIL',error=str(e),traceback=traceback.format_exc());print(result['traceback'],flush=True)
finally:
 if len(saved)==6:b.setJoints(saved)
 r.Render(True);result['logs']=logs;(out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('RESULT',result['result'],out/'result.json',flush=True)
