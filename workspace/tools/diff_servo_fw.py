# -*- coding: utf-8 -*-
"""对比驱动器里现存的 3.1.5.0 与官方 3.2.D.8，看新版多了什么代码段/字符串。"""
import hashlib, re, pathlib, collections

B = pathlib.Path(r"D:\mydata\working things\机械臂控制柜数据")
OFFICIAL = pathlib.Path(r"D:\software\dobot\V1.3.4-stable\upgradeFiles\3.5.6\3.5.6.1\files\CR5_Servo_ST_FOE_V3.2.D.8.bin")

# --- 1) 从 3.1.5 全片 hex 里取应用区 ---
BASE, LAST = 0x08010000, 0x0806049B          # 由 3.1.5_candidate_upgrade/manifest.json
mem, upper = {}, 0
for line in (B / "3.1.5.hex").read_text().splitlines():
    line = line.strip()
    if not line.startswith(":"):
        continue
    b = bytes.fromhex(line[1:])
    if (sum(b) & 0xFF) != 0:
        continue
    n, addr, typ, data = b[0], (b[1] << 8) | b[2], b[3], b[4:4 + b[0]]
    if typ == 0x00:
        for i, v in enumerate(data):
            mem[upper + addr + i] = v
    elif typ == 0x04:
        import struct; upper = struct.unpack(">H", data)[0] << 16
old = bytes(mem.get(BASE + i, 0xFF) for i in range(LAST - BASE + 1))

# --- 2) 官方 3.2.D.8 载荷（去掉 32B FoE 头）---
blob = OFFICIAL.read_bytes()
new = blob[32:]

print(f"3.1.5.0 应用区 : {len(old):,} B   md5={hashlib.md5(old).hexdigest()}")
print(f"3.2.D.8 应用区 : {len(new):,} B   md5={hashlib.md5(new).hexdigest()}")
print(f"官方件整文件    : {len(blob):,} B   md5={hashlib.md5(blob).hexdigest()}")

# --- 3) 逐字节差异统计（按重叠区）---
n = min(len(old), len(new))
same = sum(1 for i in range(n) if old[i] == new[i])
print(f"\n重叠 {n:,} B 中：相同 {same:,} ({same*100/n:.1f}%)，不同 {n-same:,}")

# --- 4) 字符串集合差异 ---
def strs(b):
    return set(re.findall(rb"[ -~]{6,}", b))
so, sn = strs(old), strs(new)
only_new = {s.decode('ascii', 'replace') for s in sn - so}
only_old = {s.decode('ascii', 'replace') for s in so - sn}
print(f"\n字符串：3.1.5.0 独有 {len(only_old)}  3.2.D.8 独有 {len(only_new)}  共有 {len(so & sn)}")

def interesting(items):
    return sorted(s for s in items if re.search(r"param|Param|EEPROM|eeprom|Store|store|SDO|sdo|0x10|save|Save|cali|Cali|zero|Zero|offset|Offset", s))

print("\n--- 3.2.D.8 独有、且与参数/存储/标定相关的字符串（前 40）---")
for s in interesting(only_new)[:40]:
    print("   +", s[:110])
print("\n--- 3.1.5.0 独有、且与参数/存储/标定相关的字符串（前 25）---")
for s in interesting(only_old)[:25]:
    print("   -", s[:110])

# --- 5) 版本串 ---
for tag, data in (("3.1.5.0", old), ("3.2.D.8", new)):
    pats = collections.Counter(re.findall(rb"DS\.[0-9A-Fa-f.]+", data))
    print(f"\n{tag} 内 DS.* 版本串: {[(k.decode(), v) for k, v in pats.most_common(6)]}")
