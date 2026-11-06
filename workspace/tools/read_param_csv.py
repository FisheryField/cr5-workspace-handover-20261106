# -*- coding: utf-8 -*-
"""读官方 servoCSV/CR/param.csv，找参数名与 SDO 地址的对应，定位零点/编码器相关项。"""
import pathlib, csv, io, re, sys

P = pathlib.Path(r"D:\mydata\workspace\data\official\servoCSV\param.csv")
raw = P.read_bytes()
for enc in ("gbk", "utf-8", "utf-8-sig"):
    try:
        txt = raw.decode(enc); print(f"解码成功: {enc}"); break
    except UnicodeDecodeError:
        continue

lines = txt.splitlines()
print(f"文件 {len(raw):,} B，{len(lines)} 行")
print("\n--- 前 8 行 ---")
for l in lines[:8]:
    print("   " + l[:200])

# 表头定位
hdr = lines[0]
print(f"\n--- 表头列名 ---")
print("   " + hdr[:300])

# 找含 编码器/零点/offset/encoder/zero 的行
KEY = re.compile(r"编码器|零点|零位|偏置|偏移|offset|encoder|Encoder|zero|Zero|home|Home|多圈|单圈|绝对")
hits = [l for l in lines if KEY.search(l)]
print(f"\n--- 含 编码器/零点/offset 等关键词的行 ({len(hits)}) ---")
for l in hits[:40]:
    print("   " + l[:220])
