# -*- coding: utf-8 -*-
"""只读：通过主控 HTTP SDO 通道读 J2/J1 的 0x6062 / 0x6064 / 0x60F4 / 0x603F / 0x6041。
一次一个请求，间隔 1.2 s。结果只出现在主控日志的 readSDO 行里。"""
import json
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CTRL = "192.168.5.1"

TARGETS = [
    ("J2", 0x6062), ("J2", 0x6064), ("J2", 0x60F4),
    ("J2", 0x603F), ("J2", 0x6041), ("J2", 0x6061),
    ("J1", 0x60F4),
]


def read(name, index, sub=0):
    body = json.dumps({"body": [{"key": "addr%04X%02X" % (index, sub),
                                 "servoNum": name, "value": 0}]}).encode()
    req = urllib.request.Request(
        "http://%s:22000/settings/readServoParams" % CTRL, data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            print("%s 0x%04X -> HTTP %s (%.1fs)" % (name, index, r.status, time.time() - t0))
    except Exception as exc:  # noqa: BLE001
        print("%s 0x%04X -> EXC %s: %s" % (name, index, type(exc).__name__, exc))


for name, index in TARGETS:
    read(name, index)
    time.sleep(1.2)

# 这些 0x6xxx 对象其实也可从 PDO 里直接看，但 SDO 读一次留个日志记号
read("J2", 0x607A)
print("done")
