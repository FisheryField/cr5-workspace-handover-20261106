#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""确认 .rdk 内脚本条目是否链接磁盘路径（UTF-16 搜索）+ 退让函数比对。"""
import io, re, difflib

text = io.open(r"D:\mydata\glm-workplace\data\scripts_ref\rdk_extract.txt", encoding="utf-8", errors="replace").read()

print("== UTF-16LE 形式的磁盘路径引用 ==")
# ASCII 字符夹 \x00 = UTF-16LE
pat = re.compile(r"[A-Za-z]\x00:\x00\\\x00(?:[^\x00]\x00){3,120}")
hits = pat.findall(text)
for h in hits[:20]:
    print("  ", h.replace("\x00", ""))
print("  （共 %d 处）" % len(hits))
if not hits:
    print("  ⇒ 站内脚本全部是内嵌副本，无磁盘文件链接")

# 相对路径也查一下（如 ..\xxx.py 或 xxx.py 引用）
print()
print("== UTF-16 相对 .py 引用 ==")
pat2 = re.compile(r"(?:[\w.\-]\x00){3,60}\.\x00p\x00y\x00")
hits2 = pat2.findall(text)
for h in hits2[:20]:
    print("  ", h.replace("\x00", ""))

# 比对内嵌块06/块10 与磁盘 9/25 版的退让函数
print()
print("== 退让逻辑比对 ==")
disk = io.open(r"D:\mydata\glm-workplace\data\scripts_ref\TCP仿真_roboDK_files2.py", encoding="utf-8", errors="replace").read()
b06 = io.open(r"D:\mydata\glm-workplace\data\scripts_ref\rdk_embedded_05_lvl.py", encoding="utf-8", errors="replace").read()
b10 = io.open(r"D:\mydata\glm-workplace\data\scripts_ref\rdk_embedded_09_TCP.py", encoding="utf-8", errors="replace").read()

def retreat_fn(src):
    m = re.search(r"def _retreat_orientation_records.*?(?=\ndef |\nclass |\Z)", src, re.S)
    return m.group(0) if m else ""

fd, f6, f0 = retreat_fn(disk), retreat_fn(b06), retreat_fn(b10)
print("磁盘9/25版 退让函数长度:", len(fd))
print("内嵌块06   退让函数长度:", len(f6))
print("内嵌块10   退让函数长度:", len(f0))
print("磁盘 == 块06:", fd.strip() == f6.strip())
print("磁盘 == 块10:", fd.strip() == f0.strip())

# 块06/块10 与磁盘版整体相似度（按行）
def sim(a, b):
    la, lb = a.splitlines(), b.splitlines()
    sm = difflib.SequenceMatcher(None, la, lb)
    return sm.ratio()

print()
print("整体行相似度: 磁盘9/25 vs 块06 = %.3f" % sim(disk, b06))
print("整体行相似度: 磁盘9/25 vs 块10 = %.3f" % sim(disk, b10))
print("磁盘版行数=%d 块06行数=%d 块10行数=%d" % (disk.count(chr(10)), b06.count(chr(10)), b10.count(chr(10))))
