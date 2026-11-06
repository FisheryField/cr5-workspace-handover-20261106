# -*- coding: utf-8 -*-
import pathlib, re, collections
B = pathlib.Path(r"D:\software\dobot\V1.3.4-stable\upgradeFiles")

x = B / "3.5.6" / "3.5.6.1" / "files" / "CR_Servo_ST_XML_V3.0.0.bin"
raw = x.read_bytes()
print(f"=== {x.name} ({len(raw)} B) ===")
head = raw[:64]
print("前 64 B hex:", head.hex())
print("是否像文本:", all(32 <= c < 127 or c in (9, 10, 13, 0) for c in raw[:256]))
txt = raw.decode("utf-8", "replace")
printable = "".join(ch if ch.isprintable() or ch in "\n\r\t" else "." for ch in txt)
print("--- 可打印视图（前 700 字符）---")
print(printable[:700])

print("\n=== 3.1.5.0 vs 3.2.D.8 独有字符串抽样 ===")
import hashlib, struct
def load_old():
    BASE, LAST = 0x08010000, 0x0806049B
    mem, upper = {}, 0
    p = pathlib.Path(r"D:\mydata\working things\机械臂控制柜数据\3.1.5.hex")
    for line in p.read_text().splitlines():
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
new = (B / "3.5.6" / "3.5.6.1" / "files" / "CR5_Servo_ST_FOE_V3.2.D.8.bin").read_bytes()[32:]
so = set(re.findall(rb"[ -~]{5,}", old)); sn = set(re.findall(rb"[ -~]{5,}", new))
on = sorted(s.decode() for s in (sn - so))
oo = sorted(s.decode() for s in (so - sn))
print(f"3.2.D.8 独有 {len(on)} 条，抽样 45 条：")
for s in on[:45]: print("   +", s[:100])
print(f"\n3.1.5.0 独有 {len(oo)} 条，抽样 25 条：")
for s in oo[:25]: print("   -", s[:100])

print("\n=== 两版共有的、含版本/设备特征的串（抽样）===")
for s in sorted(so & sn)[:0]: pass
common = sorted((so & sn), key=lambda b: -len(b))[:25]
for s in common: print("   =", s.decode()[:100])
