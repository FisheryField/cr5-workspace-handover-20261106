# -*- coding: utf-8 -*-
"""离线复现：站内『TCP仿真』原码跑轨迹11（新场景：圆柱 y=-926 + 挡板在其清单外）。
方法：导出的站内源码去掉 root.mainloop() 后整体 exec（函数可用，GUI 构建副作用可接受），
再按其 GUI 同款调用 _retreat_orientation_records → _plan_continuous_trajectory(dev=500)。
起点取全零（与历次离线口径一致）。失败时打印完整异常 + 最后一条规划日志。
"""
import sys, io, json, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import RUNMODE_SIMULATE

SRC = r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump\tcpsim_20261014_094115\TCP仿真_station.py'
code = open(SRC, encoding='utf-8').read()
lines = [l for l in code.splitlines() if l.strip() != 'root.mainloop()']
print('源码 %d 行 → 剔除 mainloop 后 %d 行' % (len(code.splitlines()), len(lines)))

ns = {}
try:
    exec(compile('\n'.join(lines), 'TCP仿真_station', 'exec'), ns)
except Exception:
    print('!! exec 站内源码失败：')
    traceback.print_exc()
    sys.exit(2)
print('exec 完成；函数就位:',
      '_plan_continuous_trajectory' in ns, '_retreat_orientation_records' in ns)
print('deviation 默认 =', ns.get('MOVEJ_FALLBACK_MAX_DEVIATION_MM'))

RDK = ns['RDK']
robot = ns['robot']
records = json.load(open(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹11.json', encoding='utf-8'))
print('录入点 =', len(records))
records = ns['_retreat_orientation_records'](records)
print('展开执行点 =', len(records))

robot.setJoints([0.0] * 6)
RDK.setRunMode(RUNMODE_SIMULATE)
_last = []
def log(m):
    _last.append(str(m))
    print('  |', m)

try:
    plan = ns['_plan_continuous_trajectory'](records, float(ns['MOVEJ_FALLBACK_MAX_DEVIATION_MM']), log)
except Exception as e:
    print('\n=== 复现失败（与用户实况同类）===')
    print(type(e).__name__ + ':', e)
    print('最后日志（定位失败点）：')
    for m in _last[-6:]:
        print('   ', m)
    sys.exit(1)
print('\n=== 预检通过：%d 段（复现未失败——需比对用户实况起点/参数）===' % len(plan))
for k, step in enumerate(plan, 1):
    print('  段%-2d %-5s %-30s J6=%+.1f' % (k, step['method'], step['p2p_note'][:30], step['joints'][5]))
