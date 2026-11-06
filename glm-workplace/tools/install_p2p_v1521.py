"""Install v15.21 only after checks; no connect or motion commands."""
from pathlib import Path
from datetime import datetime
import json,hashlib,shutil,ast,io,sys,os
from robodk.robolink import *
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',line_buffering=True)
root=Path(__file__).resolve().parents[1]
out=root/'sim_scripts/rdk_station_dump/install_v1521_20261103'
formal=root/'sim_scripts/TCP真实运动_P2P版.py'
candidate=out/'TCP真实运动_P2P版.py'
ast.parse(candidate.read_text(encoding='utf-8'))
r=Robolink(port=20500)
macros=[it for it in r.ItemList(ITEM_TYPE_PROGRAM_PYTHON)
    if it.Name() in ('TCP真实运动_P2P版','TCP真实运动_P2P版_16稳定版')]
assert len(macros)==1
macro=macros[0]; canonical_name=macro.Name()
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
reports=sorted((root/'sim_scripts/rdk_station_dump').glob('traj16_v1521_check_*/result.json'))
tests=json.loads(reports[-1].read_text(encoding='utf-8'))
assert len(tests)==3
assert tests[0]['case']=='current' and tests[0]['result']=='PASS'
assert tests[1]['case']=='edited_after_current' and tests[1]['result']=='PASS'
assert tests[2]['case']=='unreachable' and tests[2]['result']=='FAIL' and '没有逆解' in tests[2]['error']
report=tests[0]
assert report['script_sha256']==hashlib.sha256(candidate.read_bytes()).hexdigest()
trajectory=Path(r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹16.json')
assert hashlib.sha256(trajectory.read_bytes()).hexdigest()==report['original_trajectory_sha256']
assert all(report['plan'][i]['method']=='MoveJ' and not report['plan'][i]['waypoints'] for i in (1,15))
assert all(s.get('direct_movl_certified') for s in report['plan'] if s.get('waypoints'))
dryrun=json.loads((out/'dispatch_dryrun.json').read_text(encoding='utf-8'))
assert len(dryrun)==5 and all(t['result']=='PASS' for t in dryrun)
stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
macro.Save(str((out/'station_before.py').resolve()))
assert (out/'station_before.py').read_bytes()==formal.read_bytes()
shutil.copy2(formal,out/'disk_before.py')
shutil.copy2(root/'sim_scripts/real_gui_log_p2p.txt',out/'real_gui_log_before.txt')
new=r.AddFile(str(candidate.resolve()))
new.setName(canonical_name+'_待启用_v1521')
new.Save(str((out/'installed_readback.py').resolve()))
assert (out/'installed_readback.py').read_bytes()==candidate.read_bytes()
macro.setName(canonical_name+'_替换前_'+stamp)
new.setName(canonical_name)
temp=formal.with_suffix('.v1521.tmp')
temp.write_bytes(candidate.read_bytes());os.replace(temp,formal)
receipt=dict(version='v15.21-20261103',source_sha256=hashlib.sha256(formal.read_bytes()).hexdigest(),
    station=r.ActiveStation().Name(),macro=canonical_name,backup_macro=macro.Name(),actual_joints_before=q2,
    tcp=130,hardware_motion_sent=False,station_file_saved=False,trajectory_modified=False,
    isolated_precheck=str(reports[-1]),precheck_result='PASS')
(out/'installation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
