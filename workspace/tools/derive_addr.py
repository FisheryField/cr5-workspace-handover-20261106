# -*- coding: utf-8 -*-
"""推导 维护工具地址串 与 ParaMapIndex 的换算关系。"""
import pathlib, re

P = pathlib.Path(r"D:\mydata\workspace\data\official\servoCSV\param.csv")
txt = P.read_bytes().decode("gbk")
maps = []
for l in txt.splitlines()[2:]:
    r = l.split(",")
    if len(r) > 10 and r[3].strip():
        try: maps.append((r[3].strip(), int(r[10]), r[9].strip()))
        except ValueError: pass

L = pathlib.Path(r"D:\software\dobot\V1.3.4-stable\Log-RobotMaintenanceTools\20260922105222.702-dbg.log")
seq = re.findall(r"completeAddress.toUpper (\S+)", L.read_text(errors="replace"))
seq = seq[:len(maps)]

def split(s):
    return int(s[:4], 16), int(s[4:], 10)      # 前 4 位十六进制索引 + 后 2 位十进制子索引

pairs = [split(s) for s in seq]
print("前 22 组 (参数, ParaMapIndex) -> (索引, 子索引):")
for i in range(min(22, len(maps))):
    print(f"   {maps[i][0]:8} map={maps[i][1]:<4} -> 0x{pairs[i][0]:04X}:{pairs[i][1]:<3} {maps[i][2]}")

# 观察索引变化点
changes = [(i, pairs[i]) for i in range(1, len(pairs)) if pairs[i][0] != pairs[i-1][0]]
print(f"\n索引变化点 {len(changes)} 个，前 6 个：")
for i, p in changes[:6]:
    print(f"   第 {i} 项起 -> 0x{p[0]:04X}:{p[1]}   (上一项 map={maps[i-1][1]}, 本项 map={maps[i][1]}, 参数 {maps[i][0]})")

# 校验公式：index = 0x2000 + map//A, sub = map%A + 1
for A in range(2, 40):
    if all(0x2000 + (m // A) == p[0] and (m % A) + 1 == p[1] for (_, m, _), p in zip(maps, pairs)):
        print(f"\n*** 公式命中: 索引 = 0x2000 + ParaMapIndex // {A}，子索引 = ParaMapIndex % {A} + 1 ***")
        break
else:
    print("\n未找到整除公式；改看前几组差值：")
    for i in range(min(8, len(pairs))):
        print(f"   map={maps[i][1]:<4} -> idx=0x{pairs[i][0]:04X} sub={pairs[i][1]}")

print("\n=== 本问题关键参数的 SDO 地址 ===")
for a, m, c in maps:
    if any(k in c for k in ("编码器位置角", "编码器校零", "内部编码器反馈脉冲计数器", "外部编码器反馈脉冲计数器", "编码器单圈分辨率", "编码器类型")):
        i = maps.index((a, m, c))
        idx, sub = pairs[i]
        print(f"   {a:8} {c:22} -> SDO 0x{idx:04X}:{sub:02d}   (ParaMapIndex={m})")
