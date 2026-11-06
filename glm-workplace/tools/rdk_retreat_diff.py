#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""归一化后比对：内嵌最大块 vs 磁盘 9/25 版；并展示退让函数全文。"""
import io, re, difflib

def norm(p):
    s = io.open(p, encoding="utf-8", errors="replace").read()
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    lines = [l.rstrip() for l in s.split("\n")]
    lines = [l for l in lines if l.strip() != ""]  # 去空行
    return "\n".join(lines)

def retreat_fn(src):
    m = re.search(r"def _retreat_orientation_records.*?(?=\ndef |\nclass |\Z)", src, re.S)
    return m.group(0).strip() if m else ""

pairs = [
    ("内嵌09_TCP", r"D:\mydata\glm-workplace\data\scripts_ref\rdk_embedded_09_TCP.py"),
    ("内嵌05_lvl", r"D:\mydata\glm-workplace\data\scripts_ref\rdk_embedded_05_lvl.py"),
]
disk = norm(r"D:\mydata\glm-workplace\data\scripts_ref\TCP仿真_roboDK_files2.py")

for name, p in pairs:
    e = norm(p)
    sm = difflib.SequenceMatcher(None, disk.split("\n"), e.split("\n"))
    print("%s 归一化后行数=%d  与磁盘9/25相似度=%.4f" % (name, e.count("\n") + 1, sm.ratio()))
    fd, fe = retreat_fn(disk), retreat_fn(e)
    print("   退让函数: 磁盘 %d 字 vs 内嵌 %d 字, 一致=%s" % (len(fd), len(fe), fd == fe))
    if fd != fe and fd and fe:
        d = list(difflib.unified_diff(fd.split("\n"), fe.split("\n"), lineterm="", n=1))
        print("   --- 退让函数差异（前 40 行）---")
        for l in d[:40]:
            print("   " + l)
    print()

print("===== 磁盘 9/25 版退让函数全文 =====")
print(retreat_fn(disk))
