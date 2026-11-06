# -*- coding: utf-8 -*-
"""只读：用厂商 HTTP 通道读 J2 驱动器的 0x6064 / 0x6062 / 0x6061 / 0x6060，
   以及当前关节角，用于跨"上电/使能"比对是否发生"定基丢失"。"""
import json
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = '192.168.5.1'
URL = 'http://%s:22000/settings/readServoParams' % HOST

BODIES = [
    {'body': [{'key': 'addr606400', 'servoNum': 'J2'}]},
    {'body': [{'key': 'addr606200', 'servoNum': 'J2'}]},
    {'body': [{'key': 'addr606100', 'servoNum': 'J2'}]},
    {'body': [{'key': 'addr606000', 'servoNum': 'J2'}]},
    {'body': [{'key': 'addr606400', 'servoNum': 'J2', 'value': 0}]},
    {'servoNum': 'J2', 'key': 'addr606400'},
]
for b in BODIES:
    data = json.dumps(b).encode()
    req = urllib.request.Request(URL, data=data, headers={'Content-Type': 'application/json'},
                                 method='POST')
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            print('%-58s -> HTTP %s %s' % (json.dumps(b)[:58], r.status,
                                           r.read()[:220].decode('utf-8', 'replace')))
    except urllib.error.HTTPError as e:
        print('%-58s -> HTTPError %s %s' % (json.dumps(b)[:58], e.code, e.reason))
    except Exception as e:  # noqa: BLE001
        print('%-58s -> EXC %s: %s' % (json.dumps(b)[:58], type(e).__name__, e))
