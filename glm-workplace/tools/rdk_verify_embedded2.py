#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Verify the imported macro's embedded body inside a saved COPY of the station.
import sys, io, struct, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from robodk import robolink

RDK = robolink.Robolink()
SAVE = r"D:\mydata\glm-workplace\data\verify_station_copy2.rdk"
RDK.Save(SAVE)

raw = open(SAVE, "rb").read()
print("copy size:", len(raw))
n = struct.unpack(">I", raw[:4])[0]
try:
    data = zlib.decompress(raw[4:4 + n])
except Exception:
    data = zlib.decompress(raw[4:])
blob_b = data  # bytes, embedded strings are UTF-16LE inside
print("decompressed:", len(blob_b))

target_u16 = "机械臂TCP仿真_副本".encode("utf-16-le")
patched = open(r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py", "rb").read().decode("utf-8")
patched_u16 = patched.encode("utf-16-le")

i = blob_b.find(target_u16)
print("macro name found at byte:", i)

p1 = "磨砂圆柱_R180_H40".encode("utf-16-le")
p2 = "'collision' in message.lower()".encode("utf-16-le")

if i >= 0:
    w = blob_b[i:i + 400000]
    print("patch1 (wheel) in macro window:", p1 in w)
    print("patch2 (guard) in macro window:", p2 in w)

print("patch2 occurrences in whole station blob:", blob_b.count(p2))
print("wheel-name occurrences in whole station blob:", blob_b.count(p1))
j = blob_b.find(patched_u16)
print("patched body verbatim in station copy at byte:", j,
      "(>=0 means the imported macro embeds exactly our patched file)")
