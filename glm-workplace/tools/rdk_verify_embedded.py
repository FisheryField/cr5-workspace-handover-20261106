#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Save a COPY of the current station into workspace, extract the embedded
# script of the imported macro from it, compare with the patched disk file.
# The user's original .rdk file is NOT touched.
import sys, io, struct, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from robodk import robolink

RDK = robolink.Robolink()
SAVE = r"D:\mydata\glm-workplace\data\verify_station_copy.rdk"
ok = RDK.Save(SAVE)
print("Save ->", ok)

raw = open(SAVE, "rb").read()
print("copy size:", len(raw))
n = struct.unpack(">I", raw[:4])[0]
blob = zlib.decompress(raw[4:4 + n]).decode("utf-8", errors="replace") if n and n < len(raw) else None
if blob is None:
    # fallback: try whole-stream
    blob = zlib.decompress(raw[4:]).decode("utf-8", errors="replace")
print("decompressed:", len(blob))

target = "机械臂TCP仿真_副本"
# embedded scripts: length-prefixed UTF-16LE; find the entry name then the following script body
nb = target.encode("utf-16-le")
i = blob.find(nb)
print("name found at:", i)
patched = open(r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py", "rb").read().decode("utf-8")

# the embedded body follows the name; search for a long python body after name
if i >= 0:
    window = blob[i:i + 400000]
    has1 = "磨砂圆柱_R180_H40" in window
    has2 = "'collision' in message.lower()" in window
    print("embedded window: patch1(wheel)=", has1, " patch2(guard)=", has2)
    # count occurrences to ensure we're looking at OUR macro's body, not the old one
    # old embedded blocks lack patch2; patch2 string should appear exactly once globally
    print("patch2 occurrences in whole blob:", blob.count("'collision' in message.lower()"))
    print("wheel-name occurrences in whole blob:", blob.count("磨砂圆柱_R180_H40"))
    # exact-body check: does the patched disk text appear verbatim (UTF-16) right after the name?
    pn = patched.encode("utf-16-le")
    j = blob.find(pn)
    print("patched body found verbatim in station copy at:", j)
