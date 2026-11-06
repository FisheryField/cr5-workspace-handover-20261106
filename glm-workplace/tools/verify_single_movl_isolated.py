"""Validate single flange-space MovL for both strokes. All robot APIs use hidden port 20501."""
from pathlib import Path
import json,io,sys,math,numpy as np
from robodk.robolink import *
from robodk.robomath import *
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',line_buffering=True)
sys.path.insert(0,'tools');import measure_traj16_clearance as mesh
p=Path('sim_scripts/rdk_station_dump/traj16_continuity_20261103');source=(p/'station_p2p.py').read_text(encoding='utf-8');prefix=source.split('root = tk.Tk()')[0].replace('RDK = Robolink()','RDK = Robolink(port=20501)');ns={};exec(compile(prefix,'offline_station','exec'),ns)
r=ns['RDK'];b=r.Item('Dobot CR5_本体与碰撞对齐130',ITEM_TYPE_ROBOT);ns['robot']=b;assert r.RunMode()==RUNMODE_SIMULATE
plan=json.loads(Path('sim_scripts/rdk_station_dump/traj16_continuity_sync_20261103_172455/result.json').read_text(encoding='utf-8'));saved=b.Joints().list();tool=b.PoseTool();frame=b.PoseFrame();rows=[]
snapshot=json.loads((p/'live_snapshot.json').read_text(encoding='utf-8'))
cy=next(x for x in snapshot['items'] if x['name']=='磨砂圆柱_R150_H50')
relative=np.linalg.inv(np.array(cy['absolute'])@np.array(cy['geometry']))@np.array(snapshot['base'])
assert np.max(abs(relative-mesh.M))<1e-5
mesh.M=relative
lower,upper,_=b.JointLimits()
try:
 for number in (9,11):
  step=plan['plan'][number-1];assert step['method']=='MoveL';start=plan['plan'][number-2]['joints'];sendq,note=ns['_movl_digit_safe_joints'](step['joints']);assert sendq is not None
  flange=b.SolveFK(sendq);b.setPoseTool(eye(4));b.setPoseFrame(eye(4));b.setJoints(start)
  fine=b.MoveL_Test(start,flange,minstep_mm=.5);assert fine==0,(number,fine)
  program=r.AddProgram('_single_flange_probe',b)
  try:
   program.setPoseTool(eye(4));program.setPoseFrame(eye(4));program.MoveJ(start);program.MoveL(sendq);b.setJoints(start)
   msg,matrix,status=program.InstructionListJoints(mm_step=.5,deg_step=.2,collision_check=COLLISION_ON)
   assert status>=0 and 'collision' not in msg.lower(),(number,status,msg)
   qs=[row[:6] for row in matrix.tr().rows];assert qs
   a=(b.SolveFK(start)*tool).Pos();end=(b.SolveFK(step['joints'])*tool).Pos();maxdev=max(norm(subs3((b.SolveFK(q)*tool).Pos(),add3(a,mult3(subs3(end,a),max(0,min(1,dot(subs3((b.SolveFK(q)*tool).Pos(),a),subs3(end,a))/dot(subs3(end,a),subs3(end,a)))))))) for q in qs)
   assert all(ns['_real_limit_ok'](q,lower.list(),upper.list()) and not ns['_real_interfere_combo'](q) for q in qs)
   gap=min(mesh.clearance(q) for q in qs);maxjump=max(max(abs(x-y) for x,y in zip(q1,q2)) for q1,q2 in zip(qs,qs[1:]))
   rec=dict(point=number,samples=len(qs),native_status=fine,program_status=status,max_tcp_deviation_mm=maxdev,min_sampled_tool_cylinder_gap_mm=gap,max_joint_sample_jump_deg=maxjump,flange_target=Pose_2_Fanuc(flange),send_joints=sendq,digit_note=note,start_joints=start,end_joints=qs[-1],controller_command='MovL('+','.join('%.6f'%v for v in Pose_2_Fanuc(flange))+')',joints=qs)
   rows.append(rec);print(json.dumps({k:v for k,v in rec.items() if k!='joints'},ensure_ascii=False),flush=True)
  finally:program.Delete();b.setPoseTool(tool);b.setPoseFrame(frame)
finally:b.setPoseTool(tool);b.setPoseFrame(frame);b.setJoints(saved)
(p/'single_movl_validation.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
