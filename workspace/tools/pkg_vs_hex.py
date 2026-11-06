#!/usr/bin/env python3
"""CHECK C (deep): is our FoE payload really the drive's content?

The self-made package was derived from 3.1.5.hex.  If the derivation dropped or
shifted bytes, a reflash of this package would write WRONG code into the drive -
the worst possible outcome for the go/no-go test.  So verify:

  1. parse 3.1.5.hex into an address -> byte map (respecting extended-linear-
     address records, and NOT assuming record order)
  2. compare the region the package covers against the package payload
  3. also report what the hex contains BELOW the package start (the bootloader
     region the FoE write does not touch)

Any mismatch invalidates using this package for the reflash test.
"""
import re
import struct
import hashlib

HEX = "data/servo_fw_samples/3.1.5.hex"
PKG = "data/servo_fw_samples/CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin"

# ---- parse the Intel HEX ----
mem = {}
upper = 0
nrec = 0
bad = 0
for line in open(HEX, "r", errors="replace"):
    line = line.strip()
    if not line.startswith(":"):
        continue
    try:
        b = bytes.fromhex(line[1:])
    except ValueError:
        bad += 1
        continue
    n, addr, typ = b[0], (b[1] << 8) | b[2], b[3]
    data = b[4:4 + n]
    if (sum(b) & 0xFF) != 0:
        bad += 1
    if typ == 4:
        upper = ((data[0] << 8) | data[1]) << 16
    elif typ == 0:
        base = upper + addr
        for k, v in enumerate(data):
            mem[base + k] = v
        nrec += 1

print("=" * 78)
print("3.1.5.hex 解析")
print("=" * 78)
print("  数据记录 %d 条, 校验失败 %d 条" % (nrec, bad))
lo, hi = min(mem), max(mem)
print("  覆盖地址 0x%08x .. 0x%08x  (%d 字节)" % (lo, hi + 1, len(mem)))

pkg = open(PKG, "rb").read()
payload = pkg[0x20:]

# the package payload is a contiguous image; work out which flash address 0 maps to
# by matching a distinctive window (the vector table) - but also just try the两种候选
print()
for name, start in (("0x08000000", 0x08000000), ("0x08010000", 0x08010000)):
    ok = 0
    n = min(len(payload), 0x1000)
    for k in range(n):
        if mem.get(start + k) == payload[k]:
            ok += 1
    print("  假设 payload 起始 = %s : 前 0x%x 字节匹配 %d (%.1f%%)"
          % (name, n, ok, 100.0 * ok / n))
print()

# full-region compare at the start address that matched best
START = 0x08000000
mism = []
for k, v in enumerate(payload):
    a = START + k
    if mem.get(a) != v:
        mism.append((a, mem.get(a), v))
print("=" * 78)
print("完整比对（payload 起始 = 0x%08x, 长度 %d）" % (START, len(payload)))
print("=" * 78)
print("  不一致字节数: %d" % len(mism))
for a, h, p in mism[:20]:
    print("    0x%08x  hex=%s  pkg=%s" % (a, ("%02x" % h) if h is not None else "--", "%02x" % p))
print()

# what's below the package start (bootloader)
below = [(a, v) for a, v in mem.items() if a < START]
print("  hex 中位于 payload 起始之下的字节: %d" % len(below))
if below:
    blo = min(a for a, _ in below)
    bhi = max(a for a, _ in below)
    nonff = sum(1 for _, v in below if v != 0xFF)
    print("    范围 0x%08x .. 0x%08x, 非 0xFF 字节 %d" % (blo, bhi + 1, nonff))
print()

print("=" * 78)
print("结论")
print("=" * 78)
if not mism:
    print("  ✅ 包 payload 与 3.1.5.hex 在 0x%08x 起逐字节一致" % START)
    print("     => 这个包就是驱动器上 3.1.5.0 的忠实副本，可用于空刷测试")
else:
    print("  ❌ 存在 %d 处不一致 => 该包不是镜像的忠实副本，**不可用于刷写**" % len(mism))
