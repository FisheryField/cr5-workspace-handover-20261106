#!/usr/bin/env python3
"""解析 RoboDK .rdk 站点文件：解压 + 枚举长度前缀 UTF-16 字符串。

用法:
  python tools/rdk_parse.py <file.rdk>            # 概览 + 对象名清单
  python tools/rdk_parse.py <file.rdk> --strings  # 全部字符串(带偏移)
"""
import sys, struct, zlib, re
from collections import Counter


def load(path):
    raw = open(path, "rb").read()
    n = struct.unpack(">I", raw[:4])[0]
    body = raw[4:] if raw[4:6] == b"\x78\x9c" else raw
    d = zlib.decompress(body)
    assert len(d) == n, "length mismatch %d != %d" % (len(d), n)
    return d


def utf16_strings(d):
    """yield (offset, text) for u32-be BYTE-length + UTF-16LE bytes sequences."""
    i, out = 0, []
    while i + 4 <= len(d):
        n = struct.unpack(">I", d[i:i + 4])[0]
        if 0 < n <= 8192 and n % 2 == 0 and (i + 4 + n) <= len(d):
            chunk = d[i + 4:i + 4 + n]
            if chunk[1::2] == b"\x00" * (n // 2):
                try:
                    t = chunk.decode("utf-16-le")
                    if t.isprintable() or all(c.isprintable() for c in t[:64]):
                        out.append((i, t))
                        i += 4 + n
                        continue
                except UnicodeDecodeError:
                    pass
        i += 1
    return out


ROBOT_HINTS = ("Dobot", "CR5", "DOBOT", "Fanuc", "ABB", "UR", "KUKA", "robot")
TYPE_HINTS = ("Frame", "Tool", "TCP", "Program", "Target", "Object",
              "Curve", "Point", "Surface", "Ballbar", "Note", "Python")


def classify(strings):
    names = [t for _, t in strings]
    cnt = Counter()
    interesting = []
    for off, t in strings:
        if 1 < len(t) < 120 and not re.fullmatch(r"[\x00-\x1f]+", t):
            interesting.append((off, t))
        for h in TYPE_HINTS:
            if h.lower() in t.lower() and len(t) < 80:
                cnt[h] += 1
                break
    return cnt, interesting


def main():
    path = sys.argv[1]
    d = load(path)
    print("decompressed %d bytes" % len(d))
    ss = utf16_strings(d)
    print("utf16 strings: %d" % len(ss))
    cnt, interesting = classify(ss)
    print("type keyword hits:", dict(cnt))
    print("---- first 5 strings ----")
    for off, t in ss[:5]:
        print("%08x  %r" % (off, t[:100]))
    print("---- object-like names (len 2..80, mixed case/cjk) ----")
    seen = set()
    for off, t in interesting:
        if t in seen:
            continue
        seen.add(t)
        print("%08x  %s" % (off, t))


if __name__ == "__main__":
    main()
