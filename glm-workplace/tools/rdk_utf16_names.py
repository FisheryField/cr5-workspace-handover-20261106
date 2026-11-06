#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""还原 .rdk 解压流里的 UTF-16LE 段落：列出全部可读对象名与尺寸类字段。"""
import io, re

text = io.open(r"D:\mydata\glm-workplace\data\scripts_ref\rdk_extract.txt", encoding="utf-8", errors="replace").read()

# 1) 提取所有 UTF-16LE 字符串（>=4 字符，含 CJK/ASCII），当作对象名候选
strings = []
i = 0
n = len(text)
while i < n - 1:
    if text[i] != "\x00":
        i += 1
        continue
    # 从 i-1 开始可能是 UTF-16LE 序列的结尾……改为正向扫描：找连续的 (char,\x00) 对
    j = i
    start = None
    # 回溯找序列起点
    k = i - 1
    s = []
    while k >= 1 and text[k] == "\x00" and k - 1 >= 0:
        s.append(text[k - 1])
        k -= 2
    if len(s) >= 4:
        word = "".join(reversed(s))
        strings.append((k + 1, word))
    # 跳过本 \x00
    i += 2

seen = set()
print("== UTF-16LE 对象/字段名（去重，含中文）==")
for pos, w in strings:
    if w in seen or not re.search(r"[\u4e00-\u9fffA-Za-z]", w):
        continue
    seen.add(w)
    print("  at %8d : %s" % (pos, w[:60]))
