"""Install the tested script only. No robot connection or motion is issued."""
from pathlib import Path
from datetime import datetime
import json, hashlib, shutil, ast, io, sys
from robodk.robolink import *
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',line_buffering=True)
root=Path(__file__).resolve().parents[1]
out=root/'sim_scripts/rdk_station_dump/install_v1520_20261103'
formal=root/'sim_scripts/TCP真实运动_P2P版.py'
candidate=out/'TCP真实运动_P2P版.py'
ast.parse(candidate.read_text(encoding='utf-8'))
r=Robolink(port=20500)
macro=r.Item('TCP真实运动_P2P版',ITEM_TYPE_PROGRAM_PYTHON)
robot=r.Item('Dobot CR5',ITEM_TYPE_ROBOT)
ns={}
exec(compile(formal.read_text(encoding='utf-8').split('root = tk.Tk()')[0],'read_only_feedback','exec'),ns)
q,v,mode=ns['_controller_feedback']()
q2,v2,mode2=ns['_controller_feedback']()
assert mode==mode2==5 and max(map(abs,v+v2))<1
assert max(abs(a-b) for a,b in zip(q,q2))<.05
assert ns['_controller_body_matches']()
assert abs(robot.PoseTool()[2,3]-130)<1e-7
if '--feedback-only' in sys.argv:
    (out/'feedback_before.json').write_text(json.dumps(dict(q=q2,velocity=v2,mode=mode2)),encoding='utf-8')
    print('STATIONARY',q2,mode2)
    sys.exit(0)
reports=sorted((root/'sim_scripts/rdk_station_dump').glob('traj16_v1520_check_*/result.json'))
report=json.loads(reports[-1].read_text(encoding='utf-8'))
assert report['result']=='PASS' and report['source_sha256']==hashlib.sha256(candidate.read_bytes()).hexdigest()
assert report['plan'][1]['method']=='MoveJ' and not report['plan'][1]['waypoints']
assert all(s.get('direct_movl_certified') for s in report['plan'] if s.get('waypoints'))
dryrun=json.loads((out/'dispatch_dryrun.json').read_text(encoding='utf-8'))
assert len(dryrun)==3 and all(t['result']=='PASS' for t in dryrun)
stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
macro.Save(str((out/'station_before.py').resolve()))
assert (out/'station_before.py').read_bytes()==formal.read_bytes()
shutil.copy2(formal,out/'disk_before.py')
shutil.copy2(root/'sim_scripts/real_gui_log_p2p.txt',out/'real_gui_log_before.txt')
original_mode=r.RunMode()
new=r.AddFile(str(candidate.resolve()))
new.setName('TCP真实运动_P2P版_待启用_v1520')
new.Save(str((out/'installed_readback.py').resolve()))
assert (out/'installed_readback.py').read_bytes()==candidate.read_bytes()
macro.setName('TCP真实运动_P2P版_替换前_'+stamp)
new.setName('TCP真实运动_P2P版')
formal.write_bytes(candidate.read_bytes())
receipt=dict(version='v15.20-20261103',source_sha256=hashlib.sha256(formal.read_bytes()).hexdigest(),
    station=r.ActiveStation().Name(),backup_macro=macro.Name(),actual_joints_before=q2,
    tcp=130,original_mode=original_mode,hardware_motion_sent=False,station_file_saved=False,
    hidden_precheck=str(reports[-1]),precheck_result='PASS')
(out/'installation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
