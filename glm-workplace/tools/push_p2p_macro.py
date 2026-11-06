"""把磁盘上的 P2P 宏推送到 RoboDK 站内（替换同名 Python 程序），不启动、不动硬件、不保存工作站。
   2026-11-03：用于让 J4=178 / 禁直发名单=(9,) 生效。
"""
from pathlib import Path
import datetime
import io
import sys

from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON, ITEM_TYPE_ROBOT

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
base = Path(__file__).resolve().parents[1]
source = base / 'sim_scripts/TCP真实运动_P2P版.py'
print('源文件 :', source)
print('字节数 :', source.stat().st_size)

text = source.read_text(encoding='utf-8')
for key, want in (('REAL_JOINT_LIMITS = (180.0, 180.0, 160.0, 178.0, 180.0, 360.0)', True),
                  ('MOVL_DIRECT_BLOCK_POINTS = (9,)',
                   any(l.strip().startswith('MOVL_DIRECT_BLOCK_POINTS = (9,)')
                       for l in text.splitlines())),
                  ('MOVL_SEND_TOOL_USER', True)):
    ok = (key in text) == want
    print('  断言 %-58s %s' % (key[:58], 'OK' if ok else 'FAIL'))
    assert ok, key

rdk = Robolink(port=20500)
robot = rdk.Item('', ITEM_TYPE_ROBOT)
before = (robot.Joints().list(), robot.PoseTool().rows, rdk.RunMode())
print('RoboDK 已连上 ✓  RunMode=%s' % before[2])

name = 'TCP真实运动_P2P版'
olds = [it for it in rdk.ItemList(ITEM_TYPE_PROGRAM_PYTHON) if it.Name() == name]
print('站内同名程序数 :', len(olds))
assert len(olds) == 1, '站内同名程序不是 1 个，先人工确认'

old = olds[0]
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
out = base / 'sim_scripts/rdk_station_dump' / ('p2p_push_' + stamp)
out.mkdir(parents=True, exist_ok=True)
old.Save(str(out / 'before.py'))
print('旧宏已备份 :', out / 'before.py')

new = rdk.AddFile(str(source))
try:
    new.Save(str(out / 'installed.py'))
    same = (out / 'installed.py').read_bytes() == source.read_bytes()
    print('  回读字节一致 :', 'OK' if same else 'FAIL')
    assert same
    assert before == (robot.Joints().list(), robot.PoseTool().rows, rdk.RunMode()), '推送过程中机器人状态被改了'
except BaseException:
    new.Delete()
    raise

old.setName(name + '_替换前_' + stamp)
new.setName(name)

# 回读校验：站内同名程序现在应该只有新的那个，再读一次内容比对
cur = [it for it in rdk.ItemList(ITEM_TYPE_PROGRAM_PYTHON) if it.Name() == name]
print('接管后同名程序数 :', len(cur))
assert len(cur) == 1
cur[0].Save(str(out / 'readback.py'))
rb = (out / 'readback.py').read_bytes() == source.read_bytes()
print('★ 站内回读 == 磁盘 :', 'MATCH ✓' if rb else 'MISMATCH ✗')
print('')
print('推送完成，产物目录 :', out)
print('未启动宏、未动硬件、未保存工作站 ✓')
