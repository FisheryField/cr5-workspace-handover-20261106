#!/usr/bin/env python3
"""反汇编 DobotCRDriver v310.pyc（须用 RoboDK 内嵌 Python 3.10 运行本脚本）。
用法: python tools/pyc_dis.py <in.pyc> <out.txt>
"""
import dis
import marshal
import sys


def walk(code, out, depth=0):
    ind = "  " * depth
    out.write("%s=== code: %s (file %s:%s) ===\n"
              % (ind, code.co_name, code.co_filename, code.co_firstlineno))
    dis.dis(code, file=out, depth=0)
    out.write("\n")
    for const in code.co_consts:
        if hasattr(const, "co_code"):
            walk(const, out, depth + 1)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, "rb") as f:
        header = f.read(16)
        body = f.read()
    print("header:", header.hex())
    code = marshal.loads(body)
    with open(dst, "w", encoding="utf-8", errors="replace") as out:
        walk(code, out)
    print("ok ->", dst)


if __name__ == "__main__":
    main()
