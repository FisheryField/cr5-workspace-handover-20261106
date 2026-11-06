#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Precise verification: extract the embedded body near the macro name and compare
# it byte-for-byte with the patched disk file.
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
body_start = data.find("# -*- coding: utf-8 -*-".encode("utf-8"), i)
print("name at:", i, " body start at:", body_start)

patched = open(r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py", "rb").read()
print("disk file bytes:", len(patched))

embedded = data[body_start:body_start + len(patched)]
same = embedded == patched
print("embedded[0:len] == disk file :", same)
print("exact patched whitelist line embedded:",
      "for name in ('安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R180_H40'):".encode("utf-8") in data)
print("guard patch embedded:",
      "if status < 0 or 'collision' in message.lower():".encode("utf-8") in data)
print("old vulnerable guard still present anywhere:",
      data.count("if status < 0:\n            raise ValueError('整段碰撞复核未通过".encode("utf-8")), "occurrence(s)")
if not same:
    d = next((k for k in range(min(len(patched), len(embedded))) if patched[k] != embedded[k]), -1)
    print("first diff at byte", d)
    print("disk  :", patched[max(0,d-40):d+40])
    print("embed :", embedded[max(0,d-40):d+40])
