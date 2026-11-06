from pathlib import Path
import json,datetime,hashlib,shutil
from robodk.robolink import *
root=Path(r'D:\mydata\glm-workplace');formal=root/'sim_scripts/TCP真实运动_P2P版.py'
base=root/'sim_scripts/rdk_station_dump/traj17_v1522_20261104_095649'
reports=json.loads((base/'result.json').read_text(encoding='utf-8'));report=reports[-1]
assert report['result']=='PASS' and report['case']=='30'
code=formal.read_text(encoding='utf-8-sig');assert code.split('root = tk.Tk()')[0]==(base/'station_p2p.py').read_text(encoding='utf-8')
compile(code,str(formal),'exec')
r=Robolink(port=20500);robot=r.Item('Dobot CR5',ITEM_TYPE_ROBOT)
assert not robot.Busy()
# Read-only controller feedback confirms stationary; no Connect or motion.
ns={};exec(compile(code.split('root = tk.Tk()')[0],'feedback','exec'),ns)
a,v,m=ns['_controller_feedback']();b,w,n=ns['_controller_feedback']()
assert m==n==5 and max(map(abs,v+w))<1 and max(abs(x-y) for x,y in zip(a,b))<.05
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');out=root/'sim_scripts/rdk_station_dump'/('install_v1522_'+stamp);out.mkdir()
macros=[it for it in r.ItemList(ITEM_TYPE_PROGRAM_PYTHON) if it.Name() in ('TCP真实运动_P2P版','TCP真实运动_P2P版_16稳定版')];assert len(macros)==1
old=macros[0];name=old.Name();old.Save(str(out/'station_before.py'))
traj=Path(report['file']) if 'file' in report else Path(r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹17.json')
assert hashlib.sha256(traj.read_bytes()).hexdigest()==report['original_trajectory_sha256']
candidate=Path(report['candidate_file']);x=json.loads(traj.read_text(encoding='utf-8-sig'));y=json.loads(candidate.read_text(encoding='utf-8-sig'))
assert all(s['values'][0]==t['values'][0] and s['values'][2:]==t['values'][2:] for s,t in zip(x,y))
shutil.copy2(traj,out/'trajectory17_before.json')
# Preserve full installed candidate and read it back before activation.
shutil.copy2(formal,out/'TCP真实运动_P2P版.py')
new=r.AddFile(str((out/'TCP真实运动_P2P版.py').resolve()));new.setName(name+'_待启用_v1522')
new.Save(str(out/'installed_readback.py'));assert (out/'installed_readback.py').read_bytes()==formal.read_bytes()
old.setName(name+'_替换前_'+stamp);new.setName(name)
traj.write_bytes(candidate.read_bytes())
receipt=dict(version='v15.22-20261104',macro=new.Name(),backup_macro=old.Name(),trajectory=str(traj),trajectory_sha256=hashlib.sha256(traj.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(formal.read_bytes()).hexdigest(),precheck=str(base/'result.json'),extra_y_points_2_to_5_mm=30,p4_j6_from=report['plan'][2]['joints'][5],p4_j6_to=report['plan'][3]['joints'][5],controller_joints=b,hardware_motion_sent=False,station_file_saved=False)
(out/'installation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=True));print(out/'installation.json')
