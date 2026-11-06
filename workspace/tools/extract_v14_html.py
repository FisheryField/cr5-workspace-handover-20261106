#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽取 v14版本谱系与死点定位.html 的正文（去标签），按节输出。"""
import html
import io
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\glm-workplace\v14版本谱系与死点定位.html'
raw = io.open(P, encoding='utf-8', errors='replace').read()
print('原始字节 =', len(raw.encode('utf-8')))

# 去 script/style
raw = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', raw, flags=re.S | re.I)
# 块级标签转换行
raw = re.sub(r'</(p|div|li|tr|h[1-6]|table|thead|tbody|section)>', '\n', raw, flags=re.I)
raw = re.sub(r'<br\s*/?>', '\n', raw, flags=re.I)
raw = re.sub(r'</t[dh]>', ' | ', raw, flags=re.I)
raw = re.sub(r'<[^>]+>', '', raw)
txt = html.unescape(raw)
txt = re.sub(r'[ \t]+', ' ', txt)
txt = re.sub(r'\n\s*\n+', '\n', txt).strip()
print('抽取后字符 =', len(txt))
print('总行数 =', len(txt.splitlines()))
print('=' * 70)

lines = txt.splitlines()
# 先打印目录性质的行（含 v14 的行），再打印全文分段
print('--- 含 v14 / 死点 / 铁律 / 教训 的行 ---')
for i, l in enumerate(lines, 1):
    if re.search(r'v14|死点|铁律|教训|判负|拉黑|盲区|碰撞', l):
        print('L%-4d %s' % (i, l[:200]))
