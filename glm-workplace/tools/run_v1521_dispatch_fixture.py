from pathlib import Path
import socket,time
from robodk.robolink import *
from robodk.robomath import *
for attempt in range(100):
    try:
        with socket.create_connection(('127.0.0.1',20501),timeout=.2): break
    except OSError: time.sleep(.2)
else: raise RuntimeError('No isolated simulation instance')
r=Robolink(port=20501)
assert r.PORT==20501 and not r.ItemList(ITEM_TYPE_ROBOT)
r.setRunMode(RUNMODE_SIMULATE)
b=r.AddFile(str(Path('sim_scripts/rdk_station_dump/body_alignment_20261103/final_aligned_body.robot').resolve()))
b.setName('Dobot CR5')
t=b.AddTool(transl(0,0,130),'CR5_TCP_130mm');b.setPoseTool(t);b.setPoseFrame(eye(4))
try:
    exec(compile(Path('tools/test_v1521_dispatch.py').read_text(encoding='utf-8'),str(Path('tools/test_v1521_dispatch.py').resolve()),'exec'))
finally:
    r.CloseRoboDK()
