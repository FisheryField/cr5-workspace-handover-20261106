"""Independent offline LM inverse-kinematics check using exact controller MDH."""
from pathlib import Path
import numpy as np,json,math,io,sys
from robodk.robolink import *
from robodk.robomath import Fanuc_2_Pose
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',line_buffering=True)
p=Path('sim_scripts/rdk_station_dump/body_alignment_20261103');dh=np.array(json.loads((p/'exact_mdh.json').read_text(encoding='utf-8')))
def fk(q):
 T=np.eye(4)
 for (al,a,th,d),v in zip(dh,q):
  al,th=np.radians([al,th+v]);ca,sa,ct,st=np.cos(al),np.sin(al),np.cos(th),np.sin(th)
  T=T@np.array([[ct,-st,0,a],[st*ca,ct*ca,-sa,-d*sa],[st*sa,ct*sa,ca,d*ca],[0,0,0,1]])
 return T
r=Robolink(port=20500);nom=r.Item('Dobot CR5',ITEM_TYPE_ROBOT);cand=r.Item('Dobot CR5_本体与碰撞对齐130',ITEM_TYPE_ROBOT)
plan=json.loads(Path('sim_scripts/rdk_station_dump/traj16_tcp130_20261103_154825/result.json').read_text(encoding='utf-8'))['plan']
data=json.loads(Path(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹16.json').read_text(encoding='utf-8-sig'));rng=np.random.RandomState(16);results=[]
for i in [8,9,11]:
 vals=data[i-1]['values'];target=np.array(Fanuc_2_Pose(vals).rows)@np.array(Fanuc_2_Pose([0,0,-130,0,0,0]).rows)
 seeds=[s['joints'] for s in plan[7:12]]+nom.SolveIK_All(Fanuc_2_Pose([*target[:3,3],*vals[3:]])).tr().rows
 seeds += [list(rng.uniform([-180,-120,-150,-180,-170,-360],[180,120,150,180,170,360])) for _ in range(24)]
 def residual(q):
  A=fk(q);return np.r_[A[:3,3]-target[:3,3],((A[:3,:3]-target[:3,:3])*1000).ravel()]
 best=None;success=0
 for seed in seeds:
  q=np.array(seed[:6]);lam=.001
  for k in range(100):
   y=residual(q);cost=np.linalg.norm(y)
   if cost<1e-5:break
   J=np.column_stack([(residual(q+np.eye(6)[j]*1e-4)-y)/1e-4 for j in range(6)])
   dx=np.linalg.solve(J.T@J+np.eye(6)*lam,-J.T@y);dx*=min(1,20/max(1e-12,np.max(np.abs(dx))))
   qn=q+dx
   if np.linalg.norm(residual(qn))<cost:q=qn;lam=max(lam/3,1e-10)
   else:lam*=10
   if lam>1e12:break
  cost=float(np.linalg.norm(residual(q)));A=fk(q);pos=float(np.linalg.norm(A[:3,3]-target[:3,3]));ang=math.degrees(math.acos(float(np.clip((np.trace(A[:3,:3].T@target[:3,:3])-1)/2,-1,1))))
  success+=cost<1e-4
  rec=dict(point=i,q=q.tolist(),weighted_residual=cost,position_mm=pos,orientation_deg=ang,nearest_pose_xyz=A[:3,3].tolist())
  if best is None or cost<best['weighted_residual']:best=rec
 best.update(seeds=len(seeds),converged_seeds=success,robodk_ik_count=cand.SolveIK_All(Fanuc_2_Pose([*target[:3,3],*vals[3:]])).size(1));results.append(best);print(json.dumps(best),flush=True)
(p/'independent_ik.json').write_text(json.dumps(results,indent=2),encoding='utf-8')

