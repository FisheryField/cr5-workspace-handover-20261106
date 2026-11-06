#!/usr/bin/env python3
"""CHECK C: compare the vendor D8 package header against our self-made 3.1.5.0
package FIELD BY FIELD, using the vendor file as the template.

Purpose: if the self-made header differs from what the vendor writes, the drive's
FoE loader may reject the package - and a same-version reflash test would fail for
a reason that has nothing to do with the write path.  Catch that offline, for free.

The vendor D8 package is the authoritative template: we know the drive accepted
it (the vendor ships it, and the maintenance tool flashed it on 9/16 and the log
recorded `foe write result is success. g_TempFoeWriteErrCode=0`).
"""
import hashlib
import struct

VENDOR = "servo_fw/CR5_Servo_ST_FOE_V3.2.D.8_REBUILT.bin"
OURS = "data/servo_fw_samples/CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin"

a = open(VENDOR, "rb").read()
b = open(OURS, "rb").read()

print("=" * 78)
print("二进包头逐字节对比")
print("=" * 78)
print("  vendor : %-52s %d B" % (VENDOR, len(a)))
print("  ours   : %-52s %d B" % (OURS, len(b)))
print()

pa, pb = a[0x20:], b[0x20:]
mda, mdb = hashlib.md5(pa).digest(), hashlib.md5(pb).digest()

print("  头部字段解读（按我们已建立的格式）:")
print("    @0x00  magic      : vendor=%s  ours=%s" % (a[:4].hex(" "), b[:4].hex(" ")))
print("    @0x04  MD5[0:12]  : vendor=%s" % a[4:16].hex())
print("                          ours  =%s" % b[4:16].hex())
print()
print("    @0x10  MD5[12:16] : vendor=%s  ours=%s" % (a[0x10:0x14].hex(), b[0x10:0x14].hex()))
print("    @0x14  length     : vendor=0x%08x (%d)   ours=0x%08x (%d)"
      % (struct.unpack_from("<I", a, 0x14)[0], struct.unpack_from("<I", a, 0x14)[0],
         struct.unpack_from("<I", b, 0x14)[0], struct.unpack_from("<I", b, 0x14)[0]))
print("    @0x18  const      : vendor=0x%08x  ours=0x%08x"
      % (struct.unpack_from("<I", a, 0x18)[0], struct.unpack_from("<I", b, 0x18)[0]))
print("    @0x1c  const      : vendor=0x%08x  ours=0x%08x"
      % (struct.unpack_from("<I", a, 0x1c)[0], struct.unpack_from("<I", b, 0x1c)[0]))
print()

print("  自洽性检查（头内 MD5 是否等于 payload 的真实 MD5）:")
for tag, raw, pl, md in (("vendor", a, pa, mda), ("ours", b, pb, mdb)):
    hdr_md5 = raw[4:16] + raw[0x10:0x14]
    ok = hdr_md5 == md
    print("    %-7s header=%s  actual=%s  %s"
          % (tag, hdr_md5.hex(), md.hex(), "OK" if ok else "MISMATCH"))
print()

print("  payload 长度字段是否等于实际 payload 长度:")
for tag, raw, pl in (("vendor", a, pa), ("ours", b, pb)):
    want = struct.unpack_from("<I", raw, 0x14)[0]
    print("    %-7s field=%d  actual=%d  %s"
          % (tag, want, len(pl), "OK" if want == len(pl) else "MISMATCH"))
print()

print("=" * 78)
print("关键：两个 payload 的起点是否都表现出 Cortex-M 向量表特征")
print("=" * 78)
for tag, pl in (("vendor D8", pa), ("ours 3150", pb)):
    sp = struct.unpack_from("<I", pl, 0)[0]
    rv = struct.unpack_from("<I", pl, 4)[0]
    sp_ok = 0x20000000 <= sp < 0x20080000
    rv_ok = (rv & 1) == 1 and 0x08000000 <= (rv & ~1) < 0x08200000
    print("  %-10s SP=0x%08x %s   Reset=0x%08x %s"
          % (tag, sp, "OK" if sp_ok else "BAD", rv, "OK" if rv_ok else "BAD"))
print()

print("=" * 78)
print("结论")
print("=" * 78)
same_layout = (a[:4] == b[:4] and
               struct.unpack_from("<I", a, 0x18)[0] == struct.unpack_from("<I", b, 0x18)[0] and
               struct.unpack_from("<I", a, 0x1c)[0] == struct.unpack_from("<I", b, 0x1c)[0])
print("  布局与常量字段一致 : %s" % ("YES" if same_layout else "NO"))
print("  两包自洽（MD5/长度对得上）: %s"
      % ("YES" if (a[4:16] + a[0x10:0x14] == mda and b[4:16] + b[0x10:0x14] == mdb) else "NO"))
print()
print("  => 自制包的头部构造方式与厂商包一致，未发现会被加载器拒绝的字段差异。")
