"""Search common Y/Z offsets for P8-P11, without changing X/orientation or original file."""
from robodk.robolink import *
from robodk.robomath import *
from pathlib import Path
import json,math,io,sys,hashlib
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',line_buffering=True)
r=Robolink(port=20500);station=next(s for s in r.getOpenStations() if s.Name()=='轨迹16_控制器本体130验证');r.setActiveStation(station)
b=r.Item('Dobot CR5_本体与碰撞对齐130',ITEM_TYPE_ROBOT)
p=Path(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹16.json');data=p.read_bytes();records=json.loads(data.decode('utf-8-sig'))
out=Path('sim_scripts/rdk_station_dump/traj16_yz_20261103');out.mkdir(exist_ok=True)
tool=transl(0,0,130);saved=b.Joints().list();ranked=[]
def solutions(v):
 target=Fanuc_2_Pose(v)*invH(tool);valid=[]
 for row in b.SolveIK_All(target).tr().rows:
  q=row[:6]
  if len(q)!=6:continue
  if not (-170<=q[0]<=170 and -90<=q[1]<=90 and -150<=q[2]<=150 and -170<=q[3]<=170 and -170<=q[4]<=170):continue
  e=invH(target)*b.SolveFK(q)
  if norm(e.Pos())<=.01 and pose_angle(e)<=math.radians(.01):valid.append(q)
 return valid
try:
 for dy in [i*.5 for i in range(13)]:
  for dz in [-i*.5 for i in range(13)]:
   qs=[]
   for i in (7,8,9,10):
    v=records[i]['values'][:];v[1]+=dy;v[2]+=dz;ss=solutions(v)
    if not ss:break
    qs.append(ss)
   if len(qs)==4:
    elbow=min(max(abs(q[2]) for q in ss) for ss in qs)
    ranked.append(dict(dy=dy,dz=dz,norm_mm=math.hypot(dy,dz),elbow_best_min_deg=elbow))
 ranked.sort(key=lambda a:a['norm_mm']);(out/'search.json').write_text(json.dumps(dict(original_sha256=hashlib.sha256(data).hexdigest(),search=ranked),indent=2),encoding='utf-8')
 print('MINIMAL',ranked[:6]);print('MARGIN>=8',[a for a in ranked if a['elbow_best_min_deg']>=8][:6]);print('MARGIN>=10',[a for a in ranked if a['elbow_best_min_deg']>=10][:6])
finally:b.setJoints(saved)
