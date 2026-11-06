"""Build an aligned .robot from a backed-up local model and verify its FK.
Only replace the identified 24-double nominal MDH block in the qCompress payload.
Never connects to hardware or saves a station.
"""
import json,zlib,struct,math,io,sys
from pathlib import Path
import numpy as np
from robodk.robolink import *
from robodk.robomath import Fanuc_2_Pose,Pose_2_Fanuc
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace',line_buffering=True)
p=Path('sim_scripts/rdk_station_dump/body_alignment_20261103')
source=(p/'before.robot').read_bytes(); raw=bytearray(zlib.decompress(source[4:]));assert len(raw)==struct.unpack('>I',source[:4])[0]
nom=[[0,0,0,147],[90,0,90,0],[0,427,0,0],[0,357,-90,141],[-90,0,0,116],[90,0,180,100.5]]
target=json.loads((p/'exact_mdh.json').read_text())
print('TARGET',target)
if isinstance(target,dict):target=target['mdh']
for i,row in enumerate(nom):
 expected=[math.radians(row[0]),row[1],math.radians(row[2]),row[3]]
 actual=struct.unpack_from('<4d',raw,17600+i*160)
 assert max(abs(x-y) for x,y in zip(expected,actual))<1e-12,(i,actual)
for offset in (1600,17600):
    for i,row in enumerate(target):struct.pack_into('<4d',raw,offset+i*160,math.radians(row[0]),row[1],math.radians(row[2]),row[3])
output=p/'body_and_solver_aligned.robot';output.write_bytes(struct.pack('>I',len(raw))+zlib.compress(raw))
r=Robolink(port=20500);original=r.Item('Dobot CR5',ITEM_TYPE_ROBOT)
b=r.AddFile(str(output.resolve()),original.Parent());b.setName('Dobot CR5_本体与碰撞对齐130');b.setVisible(False);b.setAccuracyActive(True)
errors=[]
for s in json.loads((p/'fk_samples.json').read_text()):
 A=np.array(b.SolveFK(s['q']).rows);B=np.array(Fanuc_2_Pose(s['controller_pose']).rows)
 pos=float(np.linalg.norm(A[:3,3]-B[:3,3]));rot=math.degrees(math.acos(float(np.clip((np.trace(A[:3,:3].T@B[:3,:3])-1)/2,-1,1))))
 errors.append(dict(q=s['q'],position_mm=pos,angle_deg=rot))
report=dict(robot=b.Name(),samples=len(errors),max_position_mm=max(x['position_mm'] for x in errors),max_angle_deg=max(x['angle_deg'] for x in errors),errors=errors)
(p/'aligned_fk_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('FK',report['max_position_mm'],report['max_angle_deg']);assert report['max_position_mm']<1e-5 and report['max_angle_deg']<1e-5
r.Save(str((p/'verified_body_and_solver.robot').resolve()),b)
print('SAVED',b.Name())
