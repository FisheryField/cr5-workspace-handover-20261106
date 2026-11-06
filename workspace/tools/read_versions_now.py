# -*- coding: utf-8 -*-
"""只读：请求六轴 0x5000:07（固件版本字）。结果出现在主控日志的 sdo read 行。"""
import json
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CTRL = "192.168.5.1"
for i, ax in enumerate(["J1", "J2", "J3", "J4", "J5", "J6"]):
    body = json.dumps({"body": [{"key": "addr500007", "servoNum": ax, "value": 0}]}).encode()
    req = urllib.request.Request("http://%s:22000/settings/readServoParams" % CTRL, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=8).read()
        print("%s requested" % ax)
    except Exception as exc:  # noqa: BLE001
        print("%s HTTP error %s" % (ax, exc))
    if i < 5:
        time.sleep(1.2)
