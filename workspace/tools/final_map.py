# -*- coding: utf-8 -*-
import pathlib, re, collections

# 1) CSV 的 ParaMapIndex 范围
P = pathlib.Path(r"D:\mydata\workspace\data\official\servoCSV\param.csv")
txt = P.read_bytes().decode("gbk")
rows = [l.split(",") for l in txt.splitlines()[2:] if l.strip()]
maps = []
for r in rows:
    if len(r) > 10 and r[3].strip():
        try: maps.append((r[3].strip(), int(r[10]), r[9].strip()))
        except ValueError: pass
print(f"param.csv 参数行 {len(maps)} 条；ParaMapIndex 范围 {min(m[1] for m in maps)} ~ {max(m[1] for m in maps)}")
print("按 ParaMapIndex 排序的前 6 与后 6：")
for a, b, c in sorted(maps, key=lambda x: x[1])[:6]: print(f"   {a:8} map={b:<4} {c}")
for a, b, c in sorted(maps, key=lambda x: x[1])[-6:]: print(f"   {a:8} map={b:<4} {c}")
print("\n与本问题直接相关的参数：")
for kw in ("编码器位置角", "编码器校零", "内部编码器反馈脉冲计数器", "外部编码器反馈脉冲计数器", "编码器单圈分辨率", "编码器类型"):
    for a, b, c in maps:
        if kw in c:
            print(f"   {a:8} ParaMapIndex={b:<4} {c}")

# 2) 日志里 intParamIndex 的完整有序序列
L = pathlib.Path(r"D:\software\dobot\V1.3.4-stable\Log-RobotMaintenanceTools\20260922105222.702-dbg.log")
seq = re.findall(r"completeAddress.toUpper (\S+)", L.read_text(errors="replace"))
print(f"\ncompleteAddress 序列 {len(seq)} 个；前 10: {seq[:10]}；后 6: {seq[-6:]}")
bad = [s for s in seq if not re.fullmatch(r"20[0-9A-F]{4}", s)]
print(f"不符合 20xxxx 形式的: {len(bad)}  {bad[:5]}")

# 3) 验证编码假设：index=0x2000+(map>>8), sub=map&0xFF，地址串 = %04X%02X
ok = 0; bad2 = []
for i, s in enumerate(seq):
    if i >= len(maps): break
    m = maps[i][1]
    pred = f"{0x2000 + (m >> 8):04X}{m & 0xFF:02X}"
    if pred == s.upper(): ok += 1
    else: bad2.append((maps[i][0], m, s, pred))
print(f"\n按 '索引=0x2000+(map>>8), 子索引=map&0xFF' 预测：{ok}/{min(len(seq),len(maps))} 命中")
print("   不命中样例（参数, map, 日志值, 预测值）:", bad2[:5])
