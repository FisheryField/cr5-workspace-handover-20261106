#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Read back the embedded script text of the imported macro and verify both patches.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from robodk import robolink

RDK = robolink.Robolink()
macro = RDK.Item("机械臂TCP仿真_副本")
print("item:", macro.Name(), "type:", macro.Type())

code = None
for p in ("Script", "Code", "Text"):
    try:
        v = macro.setParam(p)
        if v and "Invalid" not in str(v):
            code = v
            print("read back via param:", p)
            break
    except Exception as e:
        print("param %s -> %s" % (p, e))
if code:
    ok1 = "磨砂圆柱_R180_H40" in code and "for name in ('安装台" in code
    ok2 = "'collision' in message.lower()" in code
    print("patch1 (wheel whitelist):", ok1)
    print("patch2 (guard incl. message):", ok2)
    print("length:", len(code))
else:
    print("no readback path; rely on behavioural verification + md5 of disk copy")
