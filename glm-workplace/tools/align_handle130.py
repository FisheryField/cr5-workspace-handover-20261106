"""Shift the grip component 4mm along flange Z; retain flange mounting mesh."""
import json,struct,datetime,io,sys,math
from pathlib import Path
from robodk.robolink import *
from robodk.robomath import *
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace',line_buffering=True)
r=Robolink(port=20500); r.setRunMode(RUNMODE_SIMULATE)
robot=r.Item('',ITEM_TYPE_ROBOT); old=r.Item('门把手_bs1')
assert old.Valid()
out=Path('sim_scripts/rdk_station_dump')/('handle130_align_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));out.mkdir()
pts,_=old.GetPoints(FEATURE_OBJECT_MESH)
geom=old.GeometryPose(); pose=old.Pose(); qs=robot.Joints().list()
assert old.Parent().item==robot.item
assert max(abs(a-b) for a,b in zip(Pose_2_Fanuc(geom),[0,0,159.5,-90,0,0]))<1e-5
assert max(abs(v) for v in Pose_2_Fanuc(pose))<1e-6
old.Save(str((out/'before.stl').resolve()))
(out/'before_transform.json').write_text(json.dumps(dict(pose=pose.rows,geometry=geom.rows)),encoding='utf-8')
(out/'before_mesh.json').write_text(json.dumps(pts),encoding='utf-8')
# The live mesh has two disconnected components. The entire grip lies at Y<100;
# the flange-side component lies at Y>130. No triangles cross that split.
newpts=[];moved=0
for i in range(0,len(pts),3):
    tri=pts[i:i+3]; shift=all(v[1]<100 for v in tri)
    assert shift or all(v[1]>130 for v in tri)
    for v in tri:
        newpts.append([v[0],v[1]-4 if shift else v[1],v[2]])
        moved+=int(shift)
assert moved>0
assert abs(159.5-min(v[1] for v in pts)-126)<0.001
assert abs(159.5-min(v[1] for v in newpts)-130)<0.001
buf=bytearray(b'grip +4mm flange Z; mount unchanged'.ljust(80,b' '))+struct.pack('<I',len(newpts)//3)
for i in range(0,len(newpts),3):
    a,b,c=newpts[i:i+3];u=[b[j]-a[j] for j in range(3)];v=[c[j]-a[j] for j in range(3)]
    n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=math.sqrt(sum(x*x for x in n)) or 1
    buf+=struct.pack('<12fH',*[x/length for x in n],*a,*b,*c,0)
stl=(out/'handle130.stl').resolve();stl.write_bytes(buf)
r.setRunMode(RUNMODE_SIMULATE)
new=r.AddFile(str(stl));new.setParent(robot);new.setPose(pose);new.setGeometryPose(geom)
try:
    for link in range(1,7):
        assert r.setCollisionActivePair(COLLISION_ON,robot,new,link,0)==1
    tool=r.Item('CR5_TCP_130mm',ITEM_TYPE_TOOL)
    if not tool.Valid():tool=robot.AddTool(transl(0,0,130),'CR5_TCP_130mm')
    assert max(abs(a-b) for a,b in zip(Pose_2_Fanuc(tool.PoseTool()),[0,0,130,0,0,0]))<1e-6
    robot.setPoseTool(tool)
    assert max(abs(a-b) for a,b in zip(robot.Joints().list(),qs))<0.01
except BaseException:
    new.Delete();raise
old.Delete();new.setName('门把手_bs1');new.setVisible(True)
live,_=new.GetPoints(FEATURE_OBJECT_MESH)
assert abs(159.5-min(v[1] for v in live)-130)<0.001
receipt=dict(backup=str(out/'before.stl'),grip_shift_flange_z_mm=4,tip_flange_z_mm=130,
             x_bounds=[min(v[0] for v in live),max(v[0] for v in live)],moved_vertices=moved,total_vertices=len(pts),
             tool=Pose_2_Fanuc(robot.PoseTool()),station_saved=False)
(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False));print('BACKUP',out)
