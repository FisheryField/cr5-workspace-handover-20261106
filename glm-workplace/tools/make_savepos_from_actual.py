#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓最新的驱动器实际位姿（gActualPosition），并据此生成本地 100 字节 SavePos 文件。"""
import io
import re
import struct
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
RSH = [r'C:\Program Files\PyManager\python.exe', r'D:\mydata\workspace\tools\rssh.py']
OUT = r'D:\mydata\workspace\data\savepos\SavePos_from_actual.bin'


def run(cmd):
    r = subprocess.run(RSH + [cmd], capture_output=True, text=True,
                       timeout=120, stdin=subprocess.DEVNULL)
    return (r.stdout or '') + (r.stderr or '')


D = '/dobot/userdata/CR5_sys_files/project/logs/all'
# ★ 只取【当前 log】（顺序很重要：grep 先 log 再 log.1 会让 tail 落在旧日志上）
out = run("grep -a 'PoseTrace: gRobotAxisMove.nextPos\\|PoseTrace: (PDO0x6062)\\|PoseTrace: gActualPosition' "
          "%s/log 2>/dev/null | tail -12 | cut -c1-215" % D)
print('=== 最近 12 行 PoseTrace ===')
for line in out.splitlines():
    print('  ', line.strip()[:205])

# 取最后一组三列
tri = {}
for line in out.splitlines():
    if 'nextPos' in line:
        tri['next'] = line
    elif '0x6062' in line:
        tri['dem'] = line
    elif 'gActualPosition' in line:
        tri['act'] = line


def nums(line):
    m = re.search(r':\s*([-0-9.,\s]+)\s*$', line.strip())
    return [float(x) for x in m.group(1).strip().rstrip(',').split(',')] if m else None


act = nums(tri.get('act', '')) if 'act' in tri else None
print('')
print('=== 最后一组 ===')
print('  nextPos   :', nums(tri.get('next', '')) if 'next' in tri else None)
print('  PDO0x6062 :', nums(tri.get('dem', '')) if 'dem' in tri else None)
print('  gActual   :', act)

if act and len(act) == 6:
    # 构 100 字节：6 个 little-endian float64 + 52 字节零
    body = b''.join(struct.pack('<d', v) for v in act) + b'\x00' * 52
    assert len(body) == 100, len(body)
    io.open(OUT, 'wb').write(body)
    print('')
    print('已生成（本地）:', OUT)
    print('  字节数 =', len(body))
    print('  前 48 字节 hex =', body[:48].hex(' '))
    print('  读回校验:', [struct.unpack_from('<d', body, i * 8)[0] for i in range(6)])
else:
    print('')
    print('!! 没有抓到 6 个 gActualPosition 值，未生成文件')
