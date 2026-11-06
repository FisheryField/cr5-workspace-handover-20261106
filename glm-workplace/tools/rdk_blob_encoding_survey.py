#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Encoding survey of the saved station copy: where are the macro body and object names?
import sys, io, struct, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

raw = open(r"D:\mydata\glm-workplace\data\verify_station_copy2.rdk", "rb").read()
n = struct.unpack(">I", raw[:4])[0]
try:
    data = zlib.decompress(raw[4:4 + n])
except Exception:
    data = zlib.decompress(raw[4:])
print("blob bytes:", len(data))

probes = {
    "wheel name": "磨砂圆柱_R180_H40",
    "old whitelist": "安装台_650x650x80mm",
    "script marker": "def _enable_obstacle_checks",
    "patch1 marker": "磨砂圆柱_R180_H40', ",
    "macro name": "机械臂TCP仿真_副本",
}
encs = {
    "utf-16le": lambda s: s.encode("utf-16-le"),
    "utf-16be": lambda s: s.encode("utf-16-be"),
    "utf-8": lambda s: s.encode("utf-8"),
    "gbk": lambda s: s.encode("gbk", errors="ignore"),
}
for label, s in probes.items():
    row = []
    for enc, fn in encs.items():
        b = fn(s)
        c = data.count(b)
        row.append("%s=%d@%s" % (enc, c, data.find(b)))
    print("%-16s %s" % (label, "  ".join(row)))
