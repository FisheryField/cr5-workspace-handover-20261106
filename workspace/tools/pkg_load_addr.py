#!/usr/bin/env python3
"""DECISIVE: at which flash address does our payload match 3.1.5.hex?

Earlier I concluded "the payload loads at 0x08000000" because its first dword is
a plausible stack pointer (0x20017a40).  That was an INFERENCE, not a measurement.
The measurement says otherwise: the first 0x1000 bytes match 0x08010000 at 100%
and 0x08000000 at 5%.

This script settles it by comparing the WHOLE payload at both candidate addresses,
and by decoding the vector table at the matching location, so the conclusion rests
on a full-length measurement rather than one dword.
"""
import struct

HEX = "data/servo_fw_samples/3.1.5.hex"
PKG = "data/servo_fw_samples/CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin"

mem = {}
upper = 0
for line in open(HEX, "r", errors="replace"):
    line = line.strip()
    if not line.startswith(":"):
        continue
    try:
        b = bytes.fromhex(line[1:])
    except ValueError:
        continue
    n, addr, typ = b[0], (b[1] << 8) | b[2], b[3]
    data = b[4:4 + n]
    if typ == 4:
        upper = ((data[0] << 8) | data[1]) << 16
    elif typ == 0:
        base = upper + addr
        for k, v in enumerate(data):
            mem[base + k] = v

pkg = open(PKG, "rb").read()
payload = pkg[0x20:]

print("payload 长度 = %d" % len(payload))
print()
print("%-14s %-14s %-14s %s" % ("candidate", "matching", "total", "result"))
for start in (0x08000000, 0x08010000, 0x08008000, 0x08020000):
    ok = sum(1 for k, v in enumerate(payload) if mem.get(start + k) == v)
    print("  0x%08x   %-14d %-14d %.1f%%" % (start, ok, len(payload),
                                             100.0 * ok / len(payload)))
print()

START = 0x08010000
ok = sum(1 for k, v in enumerate(payload) if mem.get(START + k) == v)
print("=> 全长度匹配率在 0x%08x 处 = %.4f%% (%d/%d)"
      % (START, 100.0 * ok / len(payload), ok, len(payload)))

# decode the vector table at the matching address to cross-check
print()
print("=== 在 0x%08x 处的向量表 ===" % START)
names = ["SP", "Reset", "NMI", "HardFault", "MemManage", "BusFault", "UsageFault"]
for k in range(7):
    o = START - 0x08000000 + k * 4
    v = int.from_bytes(bytes(mem[o:o + 4]), "little")
    print("   [%d] %-12s 0x%08x" % (k, names[k], v))

# and what is at 0x08000000..0x08010000 (the region FoE does NOT write)?
print()
print("=== 0x08000000..0x08010000 （FoE 不写的区域）===")
seg = bytes(mem.get(0x08000000 + k, 0xFF) for k in range(0x10000))
nonff = sum(1 for v in seg if v != 0xFF)
print("   非 0xFF 字节 %d / %d" % (nonff, len(seg)))
print("   前 32 字节: %s" % seg[:32].hex(" "))
sp = int.from_bytes(seg[0:4], "little")
rv = int.from_bytes(seg[4:8], "little")
print("   首字 SP?=0x%08x   次字 Reset?=0x%08x" % (sp, rv))
