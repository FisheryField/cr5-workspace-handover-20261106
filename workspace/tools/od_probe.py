# -*- coding: utf-8 -*-
"""1) 核实 sdo3.txt 里 3.1.5.0 驱动器的对象索引范围
   2) 在两版固件里找"索引表"痕迹，判断 3.2.D.8 是否新增厂商参数对象"""
import pathlib, re, struct, collections

WS = pathlib.Path(r"D:\mydata\workspace")

# ---------- 1) 实测 dump ----------
txt = (WS / "sdo3.txt").read_text(errors="replace")
cur = None
per = collections.defaultdict(list)
for line in txt.splitlines():
    m = re.match(r"===\s*slave\s+(\d+)\s*:\s*OD entries\s*=\s*(\d+)", line)
    if m:
        cur = int(m.group(1)); per[cur] = []; print(f"slave {cur}: 声明 {m.group(2)} 条")
        continue
    m = re.match(r"\s*(0x[0-9A-Fa-f]{4}):([0-9A-Fa-f]{2})\s", line)
    if m and cur is not None:
        per[cur].append(int(m.group(1), 16))

print("\n每从站的索引段分布：")
for s in sorted(per):
    idx = per[s]
    if not idx: continue
    rng = collections.Counter(i >> 12 for i in idx)  # 高 4 位
    seg = " ".join(f"0x{k:X}xxx:{v}" for k, v in sorted(rng.items()))
    print(f"  slave {s}: 解析 {len(idx)} 条 | {seg}")

s3 = per.get(3, [])
if s3:
    print(f"\nslave 3 全部索引去重 {len(set(s3))} 个，范围 0x{min(s3):04X}–0x{max(s3):04X}")
    print("  厂商段 0x2000-0x5FFF 的索引:", sorted({i for i in s3 if 0x2000 <= i < 0x6000}))
    print("  是否含 0x1010(Store parameters):", 0x1010 in s3)

# ---------- 2) 固件里的索引表痕迹 ----------
CAB = pathlib.Path(r"D:\mydata\working things\机械臂控制柜数据")
OFF = pathlib.Path(r"D:\software\dobot\V1.3.4-stable\upgradeFiles\3.5.6\3.5.6.1\files\CR5_Servo_ST_FOE_V3.2.D.8.bin")

def load_old():
    BASE, LAST = 0x08010000, 0x0806049B
    mem, upper = {}, 0
    for line in (CAB / "3.1.5.hex").read_text().splitlines():
        line = line.strip()
        if not line.startswith(":"): continue
        b = bytes.fromhex(line[1:])
        if sum(b) & 0xFF: continue
        n, addr, typ, data = b[0], (b[1] << 8) | b[2], b[3], b[4:4+b[0]]
        if typ == 0x00:
            for i, v in enumerate(data): mem[upper+addr+i] = v
        elif typ == 0x04:
            upper = struct.unpack(">H", data)[0] << 16
    return bytes(mem.get(BASE+i, 0xFF) for i in range(LAST-BASE+1))

def runs(data, lo, hi, minlen=6):
    """找形如 [lo,hi] 区间内单调不减的 16 位小端序列（对象索引表的特征）"""
    best, cur = [], []
    for off in range(0, len(data) - 2, 2):
        v = data[off] | (data[off+1] << 8)
        if lo <= v <= hi and (not cur or v >= cur[-1][-1]):
            cur.append((v, off))
        else:
            if len(cur) > len(best): best = cur
            cur = []
    if len(cur) > len(best): best = cur
    return best

for tag, data in (("3.1.5.0", load_old()), ("3.2.D.8", OFF.read_bytes()[32:])):
    b = runs(data, 0x2000, 0x5FFF)
    print(f"\n{tag}: 0x2000–0x5FFF 区间内最长单调索引序列 = {len(b)} 项", end="")
    if b:
        print(f"，起于 0x{b[0][1]:06X}，前 12 项: {[hex(v) for v, _ in b[:12]]}")
    else:
        print()
    for lo, hi, nm in ((0x1000, 0x1FFF, "通信对象"), (0x6000, 0x6FFF, "CiA402")):
        r = runs(data, lo, hi)
        print(f"   {nm} 段最长序列 = {len(r)} 项")
