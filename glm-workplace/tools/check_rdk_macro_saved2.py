#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Second pass: is ANY version of the TCP仿真 script embedded in today's rdk?
# Checks: names in UTF-8 vs UTF-16LE, original body embed, correct patch markers.
import sys, io, struct, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RDK = r"D:\mydata\working things\dobot_arm\RoboDK files 2\2026-9-7.rdk"
COPY = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
ORIG = r"D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂TCP仿真.py"

raw = open(RDK, "rb").read()
(ln,) = struct.unpack(">I", raw[:4])
blob = zlib.decompress(raw[4:4 + ln])
print("inflated:", len(blob))

def hits(needle):
    out, i = [], blob.find(needle)
    while i != -1:
        out.append(i)
        i = blob.find(needle, i + 1)
    return out

name = "机械臂TCP仿真"
print("\nname hits UTF-8        :", len(hits(name.encode("utf-8"))))
print("name hits UTF-16LE     :", len(hits(name.encode("utf-16-le"))))
print("name_cp hits UTF-8     :", len(hits("机械臂TCP仿真_副本".encode("utf-8"))))
print("name_cp hits UTF-16LE  :", len(hits("机械臂TCP仿真_副本".encode("utf-16-le"))))

body_cp = open(COPY, "rb").read()
body_or = open(ORIG, "rb").read()
norm = lambda b: b.replace(b"\r\n", b"\n")
print("\norig body exact embed      :", body_or in blob)
print("orig body LF-normalized    :", norm(body_or) in norm(blob))
print("copy body exact embed      :", body_cp in blob)

# correct patch markers (patch1: wheel is LAST in the tuple)
p1 = "'安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R180_H40'".encode("utf-8")
p2 = b"'collision' in message.lower()"
print("\npatch1 marker (wheel in whitelist):", len(hits(p1)), "| in disk copy:", p1 in body_cp)
print("patch2 marker (guard)             :", len(hits(p2)), "| in disk copy:", p2 in body_cp)
print("def _enable_obstacle_checks count :", len(hits("def _enable_obstacle_checks".encode("utf-8"))))
print("doc header count                  :", len(hits("单点 + 连续运动".encode("utf-8"))))

# context around each UTF-8 name hit to see how names are stored
for off in hits(name.encode("utf-8"))[:8]:
    ctx = blob[max(0, off - 40):off + 60]
    printable = "".join(chr(c) if 32 <= c < 127 else ("·" if c in (0x0a, 0x0d) else "□") for c in ctx)
    print("  ctx@%d: %s" % (off, printable))
