#!/usr/bin/env python3
"""Record the negative result in TASK_STATE.md (ASCII-only stdout).

The previous attempt died on `print()` because the Windows console codepage is
GBK and cannot encode the box-drawing/emoji characters; the AGENTS.md write in
that same script had already completed, but this half had not run.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p2 = os.path.join(ROOT, "TASK_STATE.md")
s = open(p2, encoding="utf-8").read()

ANCHOR = "\u770b `+0x20` \u534a\u5b57\u5728\u6807\u5b9a\u524d\u540e\u662f\u5426\u66fe\u4e3a 1 |"
NEWROW = (
    "\u770b `+0x20` \u534a\u5b57\u5728\u6807\u5b9a\u524d\u540e\u662f\u5426\u66fe\u4e3a 1 |\n"
    "| \u26d4\u26d4 **\u5b9e\u9a8c\u7ed3\u679c\uff082026-09-24 15:03\uff09** | "
    "**\u8865\u4e01\u65e0\u6548\uff0c\u5047\u8bf4\u88ab\u5426\u8bc1\u3002** "
    "\u5224\u636e\u5b8c\u6574\u8dd1\u8fc7\uff08\u6807\u5b9a 15:01:55 \u2192 \u4e0b\u4f7f\u80fd 15:01:58 \u2192 "
    "\u91cd\u65b0\u4e0a\u4f7f\u80fd 15:02:11\uff09\uff0c"
    "**J6 = 20.504629\u00b0 = \u539f\u59cb\u8ba1\u6570 115,054 \u00d7 scale**\uff08\u6807\u5b9a\u540e\u53c8\u5f39\u56de\uff09\uff0c"
    "\u65b0 `innerEncoder[5] = 0.0`\uff08\u5176\u4f59\u4e94\u8f74\u975e 0\uff09= \u6545\u969c\u7b7e\u540d\u4e0d\u53d8\u3002"
    "**\u21d2 \u4f4d\u7f6e\u94fe\u4e0a\u90a3\u4e2a\u4fee\u6b63\u9879\u4e0d\u662f\u96f6\u70b9\u4fdd\u6301\u7684\u4fee\u590d\u70b9\uff1b"
    "\u4f4d\u7f6e\u94fe\u91cc\u6ca1\u6709\u96f6\u70b9\u53d8\u91cf\uff0c\u8865\u4e01\u6253\u5728\u4e86\u9519\u8bef\u7684\u5c42\u3002** "
    "**\u4e0b\u4e00\u7ad9 = \u7f16\u7801\u5668\u9884\u7f6e/\u6821\u96f6\u5c42**\uff08D8 \u5b9a\u57fa\u975e\u6613\u5931 \u21d2 "
    "\u96f6\u70b9\u5199\u8fdb\u4e86\u7f16\u7801\u5668\uff09\uff1b`param.csv` \u7684 `H01.17`/`H0C.02`/`H01.18` \u662f\u5019\u9009\u3002"
    "\u5efa\u8bae\u56de\u9000 J6 \u5230\u539f\u7248\u4ee5\u4fdd\u57fa\u7ebf\u5e72\u51c0 |"
)

if ANCHOR in s and "\u5b9e\u9a8c\u7ed3\u679c\uff082026-09-24" not in s:
    s = s.replace(ANCHOR, NEWROW, 1)
    open(p2, "w", encoding="utf-8", newline="").write(s)
    sys.stdout.write("TASK_STATE.md: outcome row ADDED\n")
else:
    sys.stdout.write("TASK_STATE.md: anchor missing or already present - NOT modified\n")

b = open(p2, "rb").read()
t = b.decode("utf-8")
sys.stdout.write("TASK_STATE.md %d B  utf8 OK  U+FFFD=%d  ctrl=%d\n"
                 % (len(b), t.count("\ufffd"),
                    sum(1 for c in t if ord(c) < 32 and c not in "\n\r\t")))
