from pathlib import Path
import ast, datetime, io, sys
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON, ITEM_TYPE_ROBOT
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
base = Path(__file__).resolve().parents[1]
source = base/'sim_scripts/TCP真实运动_P2P版.py'
ast.parse(source.read_text(encoding='utf-8'))
print('Connecting to RoboDK API only',flush=True)
rdk = Robolink(port=20500)
rdk.COM.settimeout(30)
robot = rdk.Item('', ITEM_TYPE_ROBOT)
before = (robot.Joints().list(),robot.PoseTool().rows,rdk.RunMode())
items = rdk.ItemList(ITEM_TYPE_PROGRAM_PYTHON)
print('MACROS', [i.Name() for i in items],flush=True)
old, = [i for i in items if i.Name() in ('TCP真实运动_P2P版','TCP真实运动_P2P版.py')]
out = base/'sim_scripts/rdk_station_dump'/('install_v1511_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
out.mkdir(parents=True)
old.Save(str(out/'before.py'))
new = rdk.AddFile(str(source))
try:
    new.Save(str(out/'installed.py'))
    assert (out/'installed.py').read_bytes()==source.read_bytes()
    assert before==(robot.Joints().list(),robot.PoseTool().rows,rdk.RunMode())
except BaseException:
    new.Delete()
    raise
old.setName('TCP真实运动_P2P版_替换前_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
new.setName('TCP真实运动_P2P版')
print('INSTALLED',out,flush=True)
