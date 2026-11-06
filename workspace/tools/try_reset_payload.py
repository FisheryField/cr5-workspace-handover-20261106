# -*- coding: utf-8 -*-
"""试几种 modifyServoParams 的 payload 形状，找出能被接受的写法（H0C.00 故障复位）。
每个变体之间间隔 1.2 s；只打印 HTTP 状态。"""
import json
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
URL = "http://192.168.5.1:22000/settings/modifyServoParams"

VARIANTS = [
    ("value=1（我上次用的）", {"body": [{"key": "addr200C01", "servoNum": "J2", "value": 1}]}),
    ("value=0（9/18 现场抓到的写法）", {"body": [{"key": "addr200C01", "servoNum": "J2", "value": 0}]}),
    ("value=\"1\"（字符串）", {"body": [{"key": "addr200C01", "servoNum": "J2", "value": "1"}]}),
    ("加 addr 全 8 位 addr200C0100", {"body": [{"key": "addr200C0100", "servoNum": "J2", "value": 1}]}),
    ("伺服号写 J2（大写）/key 小写 c", {"body": [{"key": "addr200c01", "servoNum": "J2", "value": 1}]}),
]

for name, obj in VARIANTS:
    body = json.dumps(obj).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print("%-34s -> HTTP %s %r" % (name, r.status, r.read()[:120]))
    except urllib.error.HTTPError as exc:
        print("%-34s -> HTTPError %s %s" % (name, exc.code, exc.reason))
    except Exception as exc:  # noqa: BLE001
        print("%-34s -> EXC %s: %s" % (name, type(exc).__name__, exc))
    time.sleep(1.2)
