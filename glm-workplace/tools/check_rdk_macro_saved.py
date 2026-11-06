#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Offline, read-only: unpack today's saved .rdk (BE u32 length + zlib chunks)
# and check whether the patched macro copy is embedded and byte-identical
# to sim_scripts\机械臂TCP仿真_副本.py. Nothing is written anywhere.
import sys, io, struct, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RDK = r"D:\mydata\working things\dobot_arm\RoboDK files 2\2026-9-7.rdk"
COPY = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
ORIG = r"D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂TCP仿真.py"

raw = open(RDK, "rb").read()
print("rdk size:", len(raw))

# decompress chunk stream
blob = b""
pos, nchunks, bad = 0, 0, 0
while pos < len(raw):
    if pos + 4 > len(raw):
        break
    (ln,) = struct.unpack(">I", raw[pos:pos + 4])
    pos += 4
    try:
        blob += zlib.decompress(raw[pos:pos + ln])
        nchunks += 1
    except Exception:
        bad += 1
    pos += ln
print("chunks ok=%d bad=%d, inflated %d bytes" % (nchunks, bad, len(blob)))

def find_all(hay, needle):
    out, i = [], hay.find(needle)
    while i != -1:
        out.append(i)
        i = hay.find(needle, i + 1)
    return out

name_cp = "机械臂TCP仿真_副本".encode("utf-16-le")
name_or = "机械臂TCP仿真".encode("utf-16-le")
print("\nentry-name hits (UTF-16LE):")
print("  '机械臂TCP仿真_副本':", len(find_all(blob, name_cp)))
print("  '机械臂TCP仿真'     :", len(find_all(blob, name_or)), "(superset incl. 副本)")

body_cp = open(COPY, "rb").read()
body_or = open(ORIG, "rb").read()
print("\ndisk bodies: copy=%d B, orig=%d B" % (len(body_cp), len(body_or)))

# distinctive markers
marks = {
    "patch1 wheel whitelist (副本)": "磨砂圆柱_R180_H40', '地面_禁止穿越".encode("utf-8"),
    "patch2 collision guard (副本)": "'collision' in message.lower()".encode("utf-8"),
    "gui title line (both)": "单点 + 连续运动".encode("utf-8"),
}
for tag, m in marks.items():
    print("  marker %-30s in rdk: %d, in disk copy: %d" % (tag, len(find_all(blob, m)), m in body_cp))

# full-body containment: try exact, then CR/LF-normalized
print("\nexact copy body embedded:", body_cp in blob)
norm = lambda b: b.replace(b"\r\n", b"\n")
print("LF-normalized copy body embedded:", norm(body_cp) in norm(blob))
if body_cp in blob:
    off = blob.find(body_cp)
    print("  copy body found at inflated offset %d (0x%X)" % (off, off))
    print("  bytes before/after look like framing:", blob[off-16:off][:16].hex(), "...")
