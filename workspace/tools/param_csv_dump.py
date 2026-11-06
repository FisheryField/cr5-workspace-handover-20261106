#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump every H-group servo parameter from the vendor param.csv so the entries
can be scanned for a user-zero / multi-turn-offset style parameter."""
import io
import os
import re

SRC = (r"D:\software\dobot\V1.3.4-stable\upgradeFiles\3.5.6\3.5.6.1"
       r"\servoCSV\CR\param.csv")
OUT = r"D:\mydata\workspace\data\param_all.txt"

KW = ["零点", "零位", "绝对", "多圈", "单圈", "偏移", "位置", "编码器",
      "回零", "参考点", "偏置", "原点", "标定", "校准", "校零"]


def main():
    t = open(SRC, "rb").read().decode("gbk", "replace")
    rows = []
    for line in t.splitlines():
        f = line.split(",")
        if len(f) < 11:
            continue
        idx = f[3].strip()
        if not re.match(r"^H[0-9A-F]{2}\.\d\d$", idx):
            continue
        rows.append((idx, f[1].strip(), f[4].strip(), f[9].strip()))
    with io.open(OUT, "w", encoding="utf-8") as out:
        out.write("total %d H parameters\n\n" % len(rows))
        out.write("=== entries matching a zero/position/encoder keyword ===\n")
        for idx, grp, dflt, name in rows:
            if any(k in name for k in KW):
                out.write("%-8s %-24s default=%-12s %s\n"
                          % (idx, grp, dflt, name))
        out.write("\n=== all entries ===\n")
        for idx, grp, dflt, name in rows:
            out.write("%-8s %-24s default=%-12s %s\n" % (idx, grp, dflt, name))
    print("wrote %s (%d rows)" % (OUT, len(rows)))


if __name__ == "__main__":
    main()
