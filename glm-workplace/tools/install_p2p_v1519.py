"""Install verified body and P2P source. Never connect or issue robot motion."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, io, sys, hashlib, shutil, os, ast, math
import numpy as np
from robodk.robolink import *
from robodk.robomath import *

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
root = Path(__file__).resolve().parents[1]
out = root/'sim_scripts/rdk_station_dump/install_v1519_20261103'
candidate = out/'TCP真实运动_P2P版.py'
ast.parse(candidate.read_text(encoding='utf-8'))
dryrun = json.loads((out/'dispatch_dryrun.json').read_text(encoding='utf-8'))
assert len(dryrun)==2 and dryrun[0]['completed']==23
report = json.loads((root/'sim_scripts/rdk_station_dump/traj16_v1518_check_20261103_174447/result.json').read_text(encoding='utf-8'))
assert report['version']=='v15.19-20261103' and report['result']=='PASS'
assert report['source_sha256']==hashlib.sha256(candidate.read_bytes()).hexdigest()
assert all(report['plan'][n-1].get('direct_movl_certified') for n in (9,11))
assert hashlib.sha256(Path(report['file']).read_bytes()).hexdigest()==report['trajectory_sha256']

r = Robolink(port=20500)
main = r.ActiveStation()
old = r.Item('Dobot CR5', ITEM_TYPE_ROBOT)
macro = r.Item('TCP真实运动_P2P版', ITEM_TYPE_PROGRAM_PYTHON)
assert old.Valid() and macro.Valid()
old_mode = r.RunMode()
macro.Save(str((out/'station_before_v1516.py').resolve()))
formal = root/'sim_scripts/TCP真实运动_P2P版.py'
assert hashlib.sha256(formal.read_bytes()).hexdigest()=='638e6e3c2b9b806cc6a1bdac2f5a22439b6376f37a3de9ac951a532fa1ff8042'
assert (out/'station_before_v1516.py').read_bytes()==formal.read_bytes()
shutil.copy2(formal, out/'disk_before_v1516.py')
r.Save(str((out/'robot_before.robot').resolve()), old)

# Only the existing read-only feedback routine is invoked here.
ns = {}
exec(compile(formal.read_text(encoding='utf-8').split('root = tk.Tk()')[0],
    'readonly_install_feedback', 'exec'), ns)
actual, velocity, mode = ns['_controller_feedback']()
assert mode==5 and max(abs(v) for v in velocity)<1, 'Controller must be stationary'
actual2, velocity2, mode2 = ns['_controller_feedback']()
assert mode2==5 and max(abs(a-b) for a,b in zip(actual,actual2))<.05
basepose, oldparent = old.PoseAbs(), old.Parent()
connection = old.ConnectionParams()  # Kept in memory; never printed.
linked = []
for item in r.ItemList(ITEM_TYPE_PROGRAM):
    if item.getLink(ITEM_TYPE_ROBOT).item==old.item:
        frame_link, tool_link = item.getLink(ITEM_TYPE_FRAME), item.getLink(ITEM_TYPE_TOOL)
        linked.append((item, frame_link, tool_link.PoseTool() if tool_link.Valid() else None))
targets = [item for item in r.ItemList(ITEM_TYPE_TARGET)
           if item.getLink(ITEM_TYPE_ROBOT).item==old.item]
stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')

# Preserve the complete original robot tree in a separate, unsaved backup station.
backups = [s for s in r.getOpenStations() if s.Name().startswith('本体更新前备份_')]
if backups:
    backup_station = backups[-1]
else:
    old.Copy()
    backup_station = r.AddStation('本体更新前备份_'+stamp)
    backup_frame = r.AddFrame('原本体基座', backup_station)
    backup_frame.setPose(basepose)
    backup_robot = r.Paste(backup_frame)
    assert backup_robot.Type()==ITEM_TYPE_ROBOT
    r.setActiveStation(main)

# The idle old GUI has been closed by the calling installer before this point.
old.Disconnect()
r.setRunMode(RUNMODE_SIMULATE)
new = None
try:
    model_path = root/'sim_scripts/rdk_station_dump/body_alignment_20261103/final_aligned_body.robot'
    new = r.AddFile(str(model_path.resolve()))
    new.setName('Dobot CR5_安装中_v1519')
    newparent = new.Parent()
    newparent.setName('Dobot CR5 Base_控制器对齐')
    newparent.setPose(basepose * invH(new.PoseAbs()) * newparent.PoseAbs())
    # Imported station rotations carry float rounding and are not perfectly
    # orthogonal; invH/acos would report an artificial angular error even for
    # identical matrices. Compare the actual base matrices directly.
    assert np.max(np.abs(np.array(basepose.rows)-np.array(new.PoseAbs().rows))) < 1e-5
    for child in old.Childs():
        child.Copy()
        r.Paste(new)
    new.setConnectionParams(*connection)
    tcp = next(c for c in new.Childs() if c.Name()=='CR5_TCP_130mm')
    new.setPoseTool(tcp)
    new.setPoseFrame(eye(4))
    new.setJoints(actual2)
    samples = json.loads((root/'sim_scripts/rdk_station_dump/body_alignment_20261103/fk_samples.json').read_text(encoding='utf-8'))
    maxpos, maxangle, maxmesh = 0., 0., 0.
    for sample in samples:
        pose = new.SolveFK(sample['q'])
        delta = invH(Fanuc_2_Pose(sample['controller_pose'])) * pose
        maxpos = max(maxpos, norm(delta.Pos()))
        maxangle = max(maxangle, math.degrees(pose_angle(delta)))
        maxmesh = max(maxmesh, norm(subs3(pose.Pos(),new.JointPoses(sample['q'])[-1].Pos())))
    assert maxpos<.001 and maxangle<.001 and maxmesh<.001
    newmacro = r.AddFile(str(candidate.resolve()))
    newmacro.setName('TCP真实运动_P2P版_待启用_v1519')
    newmacro.Save(str((out/'installed_readback.py').resolve()))
    assert (out/'installed_readback.py').read_bytes()==candidate.read_bytes()
    # Preserve references before retiring the old body.
    for target in targets:
        target.setRobot(new)
    for program, frame, tool in linked:
        program.setRobot(new)
        if frame.Valid():
            program.setPoseFrame(frame)
        if tool is not None:
            program.setPoseTool(tool)
    macro.setName('TCP真实运动_P2P版_替换前_'+stamp)
    old.Delete()
    new.setName('Dobot CR5')
    new.setVisible(True)
    newmacro.setName('TCP真实运动_P2P版')
    temp = formal.with_name('TCP真实运动_P2P版.v1519.tmp')
    temp.write_bytes(candidate.read_bytes())
    os.replace(temp, formal)
    assert formal.read_bytes()==candidate.read_bytes()
    assert len(r.ItemList(ITEM_TYPE_ROBOT))==1
    assert r.Item('门把手_bs1').Parent().item==new.item
    assert max(abs(a-b) for a,b in zip(Pose_2_Fanuc(new.PoseTool()),[0,0,130,0,0,0]))<1e-7
    receipt = dict(version='v15.19-20261103',station=main.Name(),robot=new.Name(),
        backup_station=backup_station.Name(),macro_backup=macro.Name(),
        source_sha256=hashlib.sha256(formal.read_bytes()).hexdigest(),
        trajectory_sha256=report['trajectory_sha256'],actual_joints_before=actual2,
        max_fk_position_difference_mm=maxpos,max_fk_angle_difference_deg=maxangle,
        max_collision_mesh_fk_difference_mm=maxmesh,tcp=Pose_2_Fanuc(new.PoseTool()),
        original_mode=old_mode,mode_after_install=RUNMODE_SIMULATE,
        connected=False,hardware_motion_sent=False,station_file_saved=False)
    (out/'installation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False),flush=True)
except Exception:
    # Leave the station in simulation mode if any installation check fails.
    r.setRunMode(RUNMODE_SIMULATE)
    raise
