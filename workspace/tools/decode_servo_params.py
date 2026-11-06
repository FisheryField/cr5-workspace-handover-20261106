# -*- coding: utf-8 -*-
"""解码维护工具的 intParamIndex -> SDO (index, subIndex)，并与 3.1.5.0 的 OD dump 对照。"""
import pathlib, re, collections

D = pathlib.Path(r"D:\software\dobot\V1.3.4-stable\Log-RobotMaintenanceTools")
vals = set()
for p in D.glob("*.log"):
    for m in re.findall(r"intParamIndex (\d{5,6})", p.read_text(errors="replace")):
        v = int(m)
        if v: vals.add(v)

def decode(v):
    s = str(v)
    return int(s[:-2], 16), int(s[-2:], 16)   # 前段是十六进制索引，后两位是子索引

pairs = sorted({decode(v) for v in vals})
print(f"日志中出现的不同 intParamIndex: {len(vals)} 个 -> 解码为 {len(pairs)} 个 (index, subIndex) 对")
byidx = collections.defaultdict(list)
for i, s in pairs: byidx[i].append(s)
print("\n按 SDO 索引分组：")
for i in sorted(byidx):
    subs = sorted(byidx[i])
    print(f"   索引 0x{i:04X}  子索引 {len(subs)} 个: {[hex(s) for s in subs[:12]]}{' …' if len(subs)>12 else ''}")

# --- 与 3.1.5.0 实测 dump 对照 ---
sdo = (WS := pathlib.Path(r"D:\mydata\workspace")) / "sdo3.txt"
txt = sdo.read_text(errors="replace")
dumped = set()
for m in re.finditer(r"(0x[0-9A-Fa-f]{4}):([0-9A-Fa-f]{2})", txt):
    dumped.add((int(m.group(1), 16), int(m.group(2), 16)))
dumped_idx = {i for i, _ in dumped}
print(f"\n3.1.5.0 实测 dump: {len(dumped)} 条条目 / {len(dumped_idx)} 个索引")
want = set(byidx)
print(f"维护工具需要的索引: {sorted(hex(i) for i in want)}")
print(f"其中在 3.1.5.0 dump 里存在的: {sorted(hex(i) for i in (want & dumped_idx)) or '【一个都没有】'}")
print(f"落在厂商区间 0x2000-0x5FFF 的实测索引: {sorted(hex(i) for i in dumped_idx if 0x2000 <= i < 0x6000)}")

# --- 3.2.D.8 / 3.1.5.0 固件里是否出现这些索引值 ---
import struct
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

print("\n=== 两版固件里出现 0x2000~0x2009 这两个字节序列的密度（16 位小端）===")
for tag, data in (("3.1.5.0", load_old()), ("3.2.D.8", OFF.read_bytes()[32:])):
    cnt = collections.Counter()
    for i in range(0, len(data) - 1, 2):
        v = data[i] | (data[i+1] << 8)
        if 0x2000 <= v <= 0x2009:
            cnt[v] += 1
    print(f"   {tag}: " + ", ".join(f"0x{k:04X}×{v}" for k, v in sorted(cnt.items())) or f"   {tag}: 无")
