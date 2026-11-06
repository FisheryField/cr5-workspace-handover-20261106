from pathlib import Path
import json,hashlib,datetime
from robodk.robolink import *
from robodk.robomath import *
root=Path(r'D:\mydata\glm-workplace');base=root/'sim_scripts/rdk_station_dump/clearance1mm_transition_20261104_103447';p=json.loads((base/'placement.json').read_text(encoding='utf-8'))
t=Path(p['trajectory']);assert hashlib.sha256(t.read_bytes()).hexdigest()==p['sha256']
r=Robolink(port=20500);b=r.Item('Dobot CR5',ITEM_TYPE_ROBOT);assert b.Valid() and not b.Busy()
formal=root/'sim_scripts/TCP真实运动_P2P版.py';code=formal.read_text(encoding='utf-8-sig').split('root = tk.Tk()')[0];assert code==(base/'station_p2p.py').read_text(encoding='utf-8')
ns={};exec(compile(code,'readonly','exec'),ns);q,v,m=ns['_controller_feedback']();assert m==5 and max(map(abs,v))<1, 'Controller not idle'
assert max(map(abs,q))<.5,'Controller start differs from zero-start precheck'
assert max(abs(a-b) for a,b in zip(Pose_2_Fanuc(b.PoseTool()),[0,0,130,0,0,0]))<1e-4
assert max(map(abs,Pose_2_Fanuc(b.PoseFrame())))<1e-4
out=root/'sim_scripts/rdk_station_dump'/('apply_1mm_transition_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));out.mkdir()
macro=[i for i in r.ItemList(ITEM_TYPE_PROGRAM_PYTHON) if i.Name() in ('TCP真实运动_P2P版','TCP真实运动_P2P版_16稳定版')];assert len(macro)==1
macro[0].Save(str(out/'station_script.py'));assert (out/'station_script.py').read_bytes()==formal.read_bytes()
def diff(a,b):return max(abs(a[i,j]-b[i,j]) for i in range(4) for j in range(4))
items=[]
for o in p['objects']:
 it=r.Item(o['name'],ITEM_TYPE_OBJECT);assert it.Valid();cur=it.PoseAbs();target=Mat(o['target_absolute']);assert min(diff(cur,Mat(o['before_absolute'])),diff(cur,target))<.01,'Scene differs from precheck snapshot';items.append((it,cur,target))
mode=r.RunMode();model_joints=b.Joints().list();(out/'before.json').write_text(json.dumps([dict(name=i.Name(),pose_absolute=c.rows) for i,c,tg in items],ensure_ascii=False,indent=2),encoding='utf-8')
try:
 for i,c,tg in items:i.setPoseAbs(tg)
 for i,c,tg in items:assert diff(i.PoseAbs(),tg)<.01
 assert r.RunMode()==mode and b.Joints().list()==model_joints
except:
 for i,c,tg in items:i.setPoseAbs(c)
 raise
receipt=dict(version=ns['LOG_VERSION'],trajectory=str(t),trajectory_sha256=p['sha256'],controller_joints=q,objects=[dict(name=i.Name(),base_pose=Pose_2_Fanuc(invH(b.PoseAbs())*i.PoseAbs()),max_matrix_error=diff(i.PoseAbs(),tg)) for i,c,tg in items],mode=mode,hardware_motion_sent=False,station_file_saved=False)
(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(receipt,ensure_ascii=True));print(out/'receipt.json')
