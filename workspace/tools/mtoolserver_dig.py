#!/usr/bin/env python3
"""Extract the upgrade-related constants and strings from mToolServer binary.

The controller's flash tool is /mToolServer/mToolServer (source paths inside it
name cr_factory_tool/dobot_foe.cpp + http_server.cpp + third_part/SOEM).
This digs out, from the LOCAL copy data/mToolServer.bin:
  * the HTTP routes and the port it listens on
  * the exact multipart/form field names an upload expects
  * the version-comparison logic strings ("no need to update")
  * every string mentioning FoE / slave / update, with surrounding context
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "data/mToolServer.bin")

data = open(BIN, "rb").read()
print("file: %s  (%d bytes)" % (BIN, len(data)))

# printable ASCII runs
runs = [(m.start(), m.group().decode("ascii", "replace"))
        for m in re.finditer(rb"[\x20-\x7e]{4,}", data)]
print("printable runs: %d" % len(runs))

out = []
P = out.append


def show(title, pat, ctx=0, limit=80):
    P("")
    P("=" * 78)
    P(title)
    P("=" * 78)
    rx = re.compile(pat)
    n = 0
    for off, s in runs:
        if rx.search(s):
            P("  @0x%06x  %s" % (off, s[:200]))
            n += 1
            if n >= limit:
                P("  ... (truncated)")
                break
    if n == 0:
        P("  (no match)")


show("1. HTTP routes (start with /)", r"^/[A-Za-z0-9_/.]+$", limit=200)
show("2. lines mentioning update / foe / firmware", r"(?i)(update|foe|firmware)")
show("3. 'no need to update' / version compare", r"(?i)(no need|version)")
show("4. POST / multipart / form fields", r"(?i)(multipart|form-data|filename|Content-Disposition|boundary)")
show("5. port numbers / listen", r"(?i)(listen|bind|port\s*[:=]|0\.0\.0\.0)")
show("6. singleFw / xml / slave paths", r"(?i)(singleFw|tUpdate|readXml|\.xml)")
show("7. HTTP verbs & status text", r"(?i)^(GET|POST|HTTP/1|200 OK|404)")

# 32-bit little-endian port candidates near "listen"-ish strings is hopeless;
# instead list all plausible port numbers appearing as their own string
P("")
P("=" * 78)
P("8. standalone numeric strings that could be a TCP port")
P("=" * 78)
for off, s in runs:
    if re.fullmatch(r"\d{2,5}", s):
        v = int(s)
        if 1024 <= v <= 65535:
            P("  @0x%06x  %s" % (off, s))

txt = "\n".join(out)
dst = os.path.join(ROOT, "data/servo_fw_samples/MTOOLSERVER_DIG.txt")
os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst, "w", encoding="utf-8") as f:
    f.write(txt + "\n")
print(txt.encode("ascii", "replace").decode("ascii"))
print("\n[written] %s" % dst)
