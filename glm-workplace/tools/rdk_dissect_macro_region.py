#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Dissect the region right after the macro name to find where its script body lives.
import sys, io, struct, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

raw = open(r"D:\mydata\glm-workplace\data\verify_station_copy2.rdk", "rb").read()
n = struct.unpack(">I", raw[:4])[0]
try:
    data = zlib.decompress(raw[4:4 + n])
except Exception:
    data = zlib.decompress(raw[4:])

name_u16 = "机械臂TCP仿真_副本".encode("utf-16-le")
i = data.find(name_u16)
print("name at:", i, "blob len:", len(data), "tail bytes after name:", len(data) - i)

def hexdump(b, base, width=16, rows=6):
    for r in range(rows):
        s = base + r * width
        chunk = b[s:s + width]
        if not chunk:
            break
        h = " ".join("%02X" % c for c in chunk)
        t = "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)
        print("%08X  %-47s  %s" % (s, h, t))

print("--- around name start -32 ---")
hexdump(data, max(0, i - 32), rows=4)
print("--- name end +0..96 ---")
end = i + len(name_u16)
hexdump(data, end, rows=8)

# Try: 4-byte BE length then UTF-8 body right after name
for off in (end, end + 2):
    if off + 4 <= len(data):
        ln = struct.unpack(">I", data[off:off + 4])[0]
        print("at +%d: BE u32 = %d" % (off - end, ln))
        if 0 < ln < 200000:
            body = data[off + 4:off + 4 + ln]
            print("   head:", body[:80])
            print("   has patch1:", "磨砂圆柱_R180_H40" in body.decode("utf-8", errors="ignore"))
            print("   has patch2:", "'collision' in message.lower()" in body.decode("utf-8", errors="ignore"))
