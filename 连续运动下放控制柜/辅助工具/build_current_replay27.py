import json, datetime, hashlib
from pathlib import Path
from robodk.robolink import *
from robodk.robomath import *
root=Path(r'D:\mydata\glm-workplace')
src=Path(r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹17.json')
data=src.read_bytes();records=json.loads(data.decode('utf-8-sig'));assert len(records)==27
formal=root/'sim_scripts/TCP真实运动_P2P版.py';code=formal.read_text(encoding='utf-8-sig').split('root = tk.Tk()')[0]
ns={};exec(compile(code,str(formal),'exec'),ns)
r=ns['RDK'];b=ns['robot'];assert r.PORT==20500 and r.RunMode()==RUNMODE_SIMULATE and not b.Busy()
def forbidden(*a,**k):raise RuntimeError('Hardware access disabled')
ns.update(ensure_connected=forbidden,_controller_feedback=forbidden,_live_joints=forbidden,_single_move_settle=forbidden,log=lambda t:print(t,flush=True),_file_log=lambda t:None)
saved=b.Joints().list();start=[0.]*6;tool=b.PoseTool();created=[]
old=[r.Item('轨迹17_1mm过渡版_仿真25点',ITEM_TYPE_PROGRAM),r.Item('轨迹17_1mm过渡版_TCP路径',ITEM_TYPE_OBJECT)]
pn='轨迹17_仿真27点';cn='轨迹17_27点_TCP路径'
assert all(i.Valid() for i in old) and not r.Item(pn,ITEM_TYPE_PROGRAM).Valid() and not r.Item(cn,ITEM_TYPE_OBJECT).Valid()
try:
 b.setJoints(start)
 valid=ns['_retreat_orientation_records'](ns['_validated_records'](records));plan=ns['_plan_continuous_trajectory'](valid,500.,ns['log']);ns['_assert_continuous_dispatch'](valid,start,plan,True)
 assert len(plan)==27 and src.read_bytes()==data
 out=root/'sim_scripts/rdk_station_dump'/('replay27_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));out.mkdir()
 (out/'result.json').write_text(json.dumps(dict(result='PASS',plan=plan,start_joints=start,trajectory_sha256=hashlib.sha256(data).hexdigest()),ensure_ascii=False,indent=2),encoding='utf8')
 print('PLAN_PASS',out,flush=True)
 prog=r.AddProgram(pn,b);created.append(prog);prog.setRunType(PROGRAM_RUN_ON_SIMULATOR);prog.setPoseFrame(b.Parent());prog.setPoseTool(tool)
 r.Render(False)
 for index,step in enumerate([dict(method='MoveJ',joints=start)]+plan):
  assert not step.get('rewinds')
  q=step['joints'];t=r.AddTarget('回放17_27点_%02d'%index,b.Parent(),b);created.append(t)
  t.setPoseAbs(b.PoseAbs()*b.SolveFK(q)*tool)
  if step['method']=='MoveJ':t.setAsJointTarget()
  else:t.setAsCartesianTarget()
  t.setJoints(q);t.setVisible(False);getattr(prog,step['method'])(t)
 prog.ShowInstructions(False);prog.ShowTargets(False)
 msg,samples,status=prog.InstructionListJoints(mm_step=3,deg_step=2,collision_check=COLLISION_ON)
 assert status>=0 and samples.size(1)>0 and all(samples[6,i]==0 for i in range(samples.size(1))), (status,msg)
 end=samples[:6,samples.size(1)-1].list()
 assert max(abs(a-c) for a,c in zip(end,plan[-1]['joints']))<.1
 points=[(b.PoseAbs()*b.SolveFK(samples[:6,i].list())*tool).Pos() for i in range(samples.size(1))]
 curve=r.AddCurve(points,projection_type=PROJECTION_NONE);created.append(curve);curve.setName(cn);curve.setColor([.05,.75,1.,1.]);curve.setVisible(True)
except Exception:
 for item in reversed(created):
  if item.Valid():item.Delete()
 raise
finally:
 b.setJoints(saved);r.Render(True)
for item in old:item.Delete()
print('DONE',status,len(points),prog.InstructionCount(),flush=True)
