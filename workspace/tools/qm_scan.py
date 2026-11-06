#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crude Qt .qm scanner: find a source string (UTF-16BE inside the message
records) and print the following UTF-16BE string, which is its translation.

Used to learn the Chinese menu labels for the RoboDK trace options so the
operator can be told exactly what to click.
"""
import io
import os
import re

QM = r"D:\software\RoboDK\Lang\Lang_zh.qm"
OUT = r"D:\mydata\workspace\data\robodk\lang_zh_trace_labels.txt"

SOURCES = ["Trace", "References", "Points", "Dots", "Spheres", "Lines",
           "Line", "Reset", "Trace On", "Trace References", "Show trace",
           "References Off"]


def u16be(s):
    return s.encode("utf-16-be")


def read_u16be(d, off, maxlen=200):
    out = []
    i = off
    while i + 1 < len(d) and len(out) < maxlen:
        ch = (d[i] << 8) | d[i + 1]
        if ch == 0:
            break
        out.append(ch)
        i += 2
    return "".join(chr(c) for c in out), i + 2


d = open(QM, "rb").read()
lines = ["file: %s (%d bytes)" % (QM, len(d)), ""]
for src in SOURCES:
    pat = u16be(src)
    hits = [m.start() for m in re.finditer(re.escape(pat), d)]
    lines.append("=== source %r : %d hit(s)" % (src, len(hits)))
    for off in hits[:6]:
        # the next UTF-16 string after this one
        after = off + len(pat) + 2
        try:
            nxt, end = read_u16be(d, after)
        except Exception:  # noqa: BLE001
            nxt = "?"
        # also look backwards for a context-ish string
        lines.append("    @%-8d next=%r" % (off, nxt[:60]))
        if nxt and not nxt.isascii():
            lines.append("        -> TRANSLATION: %s" % nxt[:60])
    lines.append("")

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\n".join(lines[:80]))
print("\nwrote", OUT)
