# -*- coding: utf-8 -*-
"""从两版伺服固件里抽出对象字典名称表与参数标签，直接比对。"""
import pathlib, re, struct, collections

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

old = load_old()
new = OFF.read_bytes()[32:]

# 对象字典条目名：看起来像英文短语的长串
NAME = re.compile(rb"[A-Z][A-Za-z0-9 ,()/\-]{11,60}")
def names(b):
    out = set()
    for m in NAME.findall(b):
        s = m.decode("ascii").strip()
        if " " in s and not re.search(r"[^A-Za-z0-9 ,()/\-]", s):
            out.add(s)
    return out

no, nn = names(old), names(new)
print(f"名称表条目: 3.1.5.0 = {len(no)}   3.2.D.8 = {len(nn)}   共有 {len(no & nn)}")
print(f"仅 3.2.D.8 有: {len(nn - no)}    仅 3.1.5.0 有: {len(no - nn)}")

print("\n--- 仅 3.2.D.8 有的名称（全部，按字母序）---")
for s in sorted(nn - no): print("   +", s[:90])
print("\n--- 仅 3.1.5.0 有的名称（全部）---")
for s in sorted(no - nn): print("   -", s[:90])

# 伺服参数标签 H0.00 ~ HE.12 形式
TAG = re.compile(rb"\b[A-H][0-9A-F]\.[0-9]{2}\b")
to = collections.Counter(TAG.findall(old)); tn = collections.Counter(TAG.findall(new))
print(f"\n参数标签 H0.00~HE.12 形式: 3.1.5.0 = {sum(to.values())} 条 {len(to)} 种 | 3.2.D.8 = {sum(tn.values())} 条 {len(tn)} 种")
print("  3.2.D.8 抽样:", sorted(x.decode() for x in list(tn)[:25]))
print("  3.1.5.0 抽样:", sorted(x.decode() for x in list(to)[:25]))

# 与控制器侧 dump 交叉验证
sdo = (CAB.parent.parent / "workspace" / "sdo3.txt")
if not sdo.exists():
    sdo = pathlib.Path(r"D:\mydata\workspace\sdo3.txt")
txt = sdo.read_text(errors="replace")
print(f"\n=== sdo3.txt（3.1.5.0 驱动器实测 OD dump）前 12 行 ===")
for l in txt.splitlines()[:12]: print("   " + l[:120])
dumped = set(re.findall(r"[A-Z][A-Za-z0-9 ,()/\-]{11,60}", txt))
print(f"dump 中提取到名称 {len(dumped)} 条；其中 {len(dumped & no)} 条出现在 3.1.5.0 固件名称表里（应接近全部）")
print(f"dump 名称中出现在 3.2.D.8 名称表里的: {len(dumped & nn)} 条")
