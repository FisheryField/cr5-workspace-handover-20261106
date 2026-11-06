from pathlib import Path
import json
from robodk.robolink import *
from robodk.robomath import *
p=Path('sim_scripts/rdk_station_dump/traj16_continuity_20261103')
saved=json.loads((p/'live_snapshot.json').read_text(encoding='utf-8'))
sim=Robolink(port=20501);sim.setRunMode(RUNMODE_SIMULATE)
base=sim.AddFrame('本体基座');base.setPose(Mat(saved['base']));model=sim.AddFile(str(Path('sim_scripts/rdk_station_dump/body_alignment_20261103/final_aligned_body.robot').resolve()));model.setName('Dobot CR5_本体与碰撞对齐130');parent=model.Parent();parent.setPose(Mat(saved['base'])*invH(model.PoseAbs())*parent.PoseAbs())
for item in saved['items']:
 obj=sim.AddFile(item['file']);obj.setName(item['name']);obj.setGeometryPose(Mat(item['geometry']))
 if item['is_handle']:obj.setParent(model);obj.setPose(Mat(item['pose']))
 else:obj.setPose(Mat(item['absolute']))
t=model.AddTool(transl(0,0,130),'CR5_TCP_130mm');model.setPoseTool(t);model.setPoseFrame(eye(4));print('isolated ready',sim.PORT,flush=True)
