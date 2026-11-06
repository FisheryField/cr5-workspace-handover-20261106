# -*- coding: utf-8 -*-
"""站内每个内嵌脚本块的完整画像：字节范围、长度、sha、首个 import 行，并与磁盘两份比对。"""
import hashlib, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = open(r'D:\mydata\workspace\_rdk_unpacked.bin', 'rb').read()
starts = [m.start() for m in re.finditer(rb'from robodk\.robolink import \*', d)]
# 每个块的起点往前退到文件头（脚本块的真正起点在 import 之前）
offs = [663, 1861423, 1910630, 1959618, 2013647, 2050611, 2125607,
        2179227, 2233776, 2290613, 2355833, 2410523, 2473317]

refs = {
    'workspace 机械臂TCP真实运动.py': r'D:\mydata\workspace\机械臂TCP真实运动.py',
    'RoboDK目录 机械臂TCP真实运动.py': r'D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂TCP真实运动.py',
    'RoboDK目录 机械臂法兰真实运动.py': r'D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂法兰真实运动.py',
    'RoboDK目录 9-29.py': r'D:\mydata\working things\dobot_arm\RoboDK files 2\9-29.py',
    'RoboDK目录 test.py': r'D:\mydata\working things\dobot_arm\RoboDK files 2\test.py',
    'RoboDK目录 机械臂TCP仿真.py': r'D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂TCP仿真.py',
}
refdata = {}
for k, p in refs.items():
    if os.path.exists(p):
        raw = open(p, 'rb').read()
        refdata[k] = (raw, hashlib.sha256(raw).hexdigest())
    else:
        print('缺文件:', p)

print('=== 站内 13 个 "from robodk.robolink import *" 站点解析 ===\n')
blobs = []
for i, o in enumerate(offs):
    # 向后找块结束：下一个非 python 记录的分隔（用 \x00 试，取最后一个可行）
    end = d.find(b'\x00', o)
    blob = d[o:end]
    # 有些块可能被别的记录插在中间，检查尾部是否仍像 python
    text = d[o:o+250000]
    blobs.append((i, o, end, blob))

    def sz(p):
        return os.path.getsize(p) if os.path.exists(p) else -1

    print('--- 块 %02d @%d  (到第一个 \\x00 = %d, 有效 %d B)' % (i, o, end, len(blob)))
    print('    起点前 200 B:', repr(d[max(0, o-200):o])[:260])
    # 与磁盘比对：找磁盘文件里同样的锚点偏移
    for k, (raw, h) in refdata.items():
        idx = raw.find(b'from robodk.robolink import *')
        if idx < 0:
            continue
        delta = o - idx  # 该磁盘文件整体是否是站内块
        # 校验：站内 [o:o+len(raw)-idx] 是否等于磁盘 raw[idx:]
        cand = d[o:o+len(raw)-idx]
        if cand == raw[idx:]:
            print('    ✔ 与【%s】逐字节相同（站内偏移 %d 起，长 %d）' % (k, o, len(cand)))
        elif raw in d:
            print('    ~ 【%s】整文件在站内别处（此处仅 import 行相同）' % k)
    print()
