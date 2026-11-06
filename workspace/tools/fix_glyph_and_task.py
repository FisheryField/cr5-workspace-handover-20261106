#!/usr/bin/env python3
"""Fix a wrong codepoint I introduced while condensing AGENTS.md, and record the
negative result in TASK_STATE.md §0.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# \u23d4 (\u23d4 = "up arrow double stroke") was a typo for \u26d4 (no-entry sign)
WRONG = "\u23d4"
RIGHT = "\u26d4"

p = os.path.join(ROOT, "AGENTS.md")
t = open(p, encoding="utf-8").read()
n = t.count(WRONG)
t = t.replace(WRONG, RIGHT)
open(p, "w", encoding="utf-8", newline="").write(t)
print("AGENTS.md: replaced %d x %r -> %r ; now %d bytes"
      % (n, WRONG, RIGHT, len(t.encode("utf-8"))))

# --- TASK_STATE.md: replace the round-33 pending row with the outcome ---
p2 = os.path.join(ROOT, "TASK_STATE.md")
s = open(p2, encoding="utf-8").read()
OLD = ("| \u2605 **\u672a\u9a8c\u8bc1\u7684\u6839\u56e0\u5019\u9009** | D8 \u7528 `ldrb`/`strb` \u8bfb\u5199 `0x20000020`\uff1b"
       "3150 \u7528 `ldrh` \u8bfb `0x20000020` \u5374\u628a 1 \u5199\u5230 `0x20000022` \u21d2 3150 \u7684\u201c\u4fee\u6b63\u9879\u6e05\u96f6\u201d"
       "\u8def\u5f84\u53ef\u80fd\u6c38\u8fdc\u8d70\u4e0d\u5230\u3002**\u96f6\u98ce\u9669\u9a8c\u8bc1**\uff1a\u7528 `amrd` \u8bfb "
       "`0x20000000..0x20000040`\uff0c\u770b `+0x20` \u534a\u5b57\u5728\u6807\u5b9a\u524d\u540e\u662f\u5426\u66fe\u4e3a 1 |")
NEW = ("| \u2605 **\u672a\u9a8c\u8bc1\u7684\u6839\u56e0\u5019\u9009** | D8 \u7528 `ldrb`/`strb` \u8bfb\u5199 `0x20000020`\uff1b"
       "3150 \u7528 `ldrh` \u8bfb `0x20000020` \u5374\u628a 1 \u5199\u5230 `0x20000022` \u21d2 3150 \u7684\u201c\u4fee\u6b63\u9879\u6e05\u96f6\u201d"
       "\u8def\u5f84\u53ef\u80fd\u6c38\u8fdc\u8d70\u4e0d\u5230\u3002**\u96f6\u98ce\u9669\u9a8c\u8bc1**\uff1a\u7528 `amrd` \u8bfb "
       "`0x20000000..0x20000040`\uff0c\u770b `+0x20` \u534a\u5b57\u5728\u6807\u5b9a\u524d\u540e\u662f\u5426\u66fe\u4e3a 1 |\n"
       "| \u23d4\u23d4 **\u5b9e\u9a8c\u7ed3\u679c\uff082026-09-24 15:03\uff09** | **\u8865\u4e01\u65e0\u6548\uff0c\u5047\u8bf4\u88ab\u5426\u8bc1\u3002**"
       "\u5224\u636e\u5b8c\u6574\u8dd1\u8fc7\uff08\u6807\u5b9a 15:01:55 \u2192 \u4e0b\u4f7f\u80fd 15:01:58 \u2192 \u91cd\u65b0\u4e0a\u4f7f\u80fd 15:02:11\uff09\uff0c"
       "**J6 = 20.504629\u00b0 = \u539f\u59cb\u8ba1\u6570 115,054 \u00d7 scale**\uff08\u6807\u5b9a\u540e\u53c8\u5f39\u56de\uff09\uff0c"
       "\u65b0 `innerEncoder[5] = 0.0`\uff08\u5176\u4f59\u4e94\u8f74\u975e 0\uff09= \u6545\u969c\u7b7e\u540d\u4e0d\u53d8\u3002"
       "**\u21d2 \u4f4d\u7f6e\u94fe\u4e0a\u90a3\u4e2a\u4fee\u6b63\u9879\u4e0d\u662f\u96f6\u70b9\u4fdd\u6301\u7684\u4fee\u590d\u70b9\uff1b"
       "**\u4f4d\u7f6e\u94fe\u91cc\u6ca1\u6709\u96f6\u70b9\u53d8\u91cf\uff0c\u8865\u4e01\u6253\u5728\u4e86\u9519\u8bef\u7684\u5c42**\u3002"
       "**\u4e0b\u4e00\u7ad9 = \u7f16\u7801\u5668\u9884\u7f6e/\u6821\u96f6\u5c42**\uff08D8 \u5b9a\u57fa\u975e\u6613\u5931 \u21d2 "
       "\u96f6\u70b9\u5199\u8fdb\u4e86\u7f16\u7801\u5668\uff09\uff1b`param.csv` \u7684 `H01.17`/`H0C.02`/`H01.18` \u662f\u5019\u9009\u3002"
       "\u5efa\u8bae\u56de\u9000 J6 \u5230\u539f\u7248\u4ee5\u4fdd\u57fa\u7ebf\u5e72\u51c0 |")
if OLD in s:
    s = s.replace(OLD, NEW.replace("\u23d4\u23d4", RIGHT + RIGHT))
    open(p2, "w", encoding="utf-8", newline="").write(s)
    print("TASK_STATE.md: outcome row added")
else:
    print("TASK_STATE.md: target row not found - NOT modified")

for q in (p, p2):
    b = open(q, "rb").read()
    x = b.decode("utf-8")
    print("  %-16s %7d B  utf8 OK  U+FFFD=%d  ctrl=%d"
          % (os.path.basename(q), len(b), x.count("\ufffd"),
             sum(1 for c in x if ord(c) < 32 and c not in "\n\r\t")))
