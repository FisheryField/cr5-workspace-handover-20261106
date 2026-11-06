# -*- coding: utf-8 -*-
"""比对活动目录与回收站快照，找出谁是谁的超集、哪些文件只在一边存在。

用法: python audit_data.py
"""
import hashlib, os, sys, collections

RB = r"D:\$RECYCLE.BIN\S-1-5-21-3003449410-212866346-2127617813-1001\$RRT678O"

PAIRS = [
    ("机械臂控制柜数据", r"D:\mydata\working things\机械臂控制柜数据", os.path.join(RB, r"working things\机械臂控制柜数据")),
    ("working things 整体", r"D:\mydata\working things", os.path.join(RB, "working things")),
    ("旧工作区", r"D:\mydata\workspace-旧版数据", os.path.join(RB, "Workspace")),
]

def scan(root):
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            try:
                st = os.stat(p)
            except OSError:
                continue
            out[os.path.relpath(p, root)] = st.st_size
    return out

for label, live, recy in PAIRS:
    print("=" * 78)
    print(f"### {label}")
    print(f"  活动: {live}")
    print(f"  快照: {recy}")
    if not os.path.isdir(live) or not os.path.isdir(recy):
        print(f"  !! 缺失: live={os.path.isdir(live)} recycle={os.path.isdir(recy)}")
        continue
    a, b = scan(live), scan(recy)
    sa, sb = sum(a.values()), sum(b.values())
    print(f"  活动 {len(a):5d} 文件 {sa/1048576:8.2f} MB   |   快照 {len(b):5d} 文件 {sb/1048576:8.2f} MB")
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    sizediff = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    print(f"  仅活动有 {len(only_a)}  |  仅快照有 {len(only_b)}  |  同名但大小不同 {len(sizediff)}")
    for tag, lst in (("仅活动", only_a), ("仅快照", only_b), ("大小不同", sizediff)):
        for k in lst[:12]:
            extra = f"  ({a.get(k,'-')} vs {b.get(k,'-')})" if tag == "大小不同" else ""
            print(f"     [{tag}] {k}{extra}")
        if len(lst) > 12:
            print(f"     [{tag}] … 其余 {len(lst)-12} 项")
