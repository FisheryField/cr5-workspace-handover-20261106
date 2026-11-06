# -*- coding: utf-8 -*-
"""只读导出站内 TCP仿真 宏源码到 rdk_station_dump，并打印结构信息（stop标记/关键函数/调用点）。"""
import sys, io, os, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink

RDK = Robolink()
it = RDK.Item('TCP仿真')
assert it.Valid(), '站内未找到 TCP仿真'
code = it.setParam('Code').replace('<br>', '\n')

d = os.path.join(r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump', 'tcpsim_' + time.strftime('%Y%m%d_%H%M%S'))
os.makedirs(d, exist_ok=True)
out = os.path.join(d, 'TCP仿真_station.py')
open(out, 'w', encoding='utf-8').write(code)
print('导出:', out, len(code), '字符')

# 磁盘副本对比
disk = r'D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py'
try:
    dcode = open(disk, encoding='utf-8').read()
    print('与磁盘副本一致:', dcode == code, '（磁盘 %d 字符）' % len(dcode))
except Exception as e:
    print('磁盘副本读取失败:', e)

lines = code.splitlines()
stop = [i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()')]
print('stop 标记 root = tk.Tk() 行号:', stop[:1])
defs = re.findall(r'^def (_\w+)\(', code, re.M)
print('下划线函数:', defs)
# 规划调用点
for m in re.finditer(r'^.*(_plan_continuous_trajectory|_retreat_orientation_records)\(.*$', code, re.M):
    print('调用点:', m.group(0).strip()[:150])
# deviation 常量/默认
for m in re.finditer(r'^.*(deviation|偏离上限).*$', code, re.M):
    s = m.group(0).strip()
    if len(s) < 160:
        print('deviation:', s)
