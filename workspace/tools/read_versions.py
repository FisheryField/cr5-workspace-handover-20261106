#!/usr/bin/env python3
"""读六轴伺服固件版本字 0x5000:07（HTTP 只读 SDO，串行，间隔 1.05s），
然后从 all/log 抓最新一条 sdo read 结果行。"""
import json, time, urllib.request, re

CTRL = "192.168.5.1"
AXES = ["J1", "J2", "J3", "J4", "J5", "J6"]
VER = {0x32D8: "3.2.D.8", 0x3150: "3.1.5.0"}


def read_log_tail(n=60):
    import subprocess, sys
    out = subprocess.run(
        [sys.executable, "tools/rssh.py",
         "grep -a 'sdo read' /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -%d" % n],
        capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    return out


def main():
    for i, ax in enumerate(AXES):
        body = json.dumps({"body": [{"key": "addr500007",
                                     "servoNum": ax, "value": 0}]}).encode()
        req = urllib.request.Request(
            "http://%s:22000/settings/readServoParams" % CTRL, data=body,
            headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=8).read()
        except Exception as e:
            print("%s: HTTP error %s" % (ax, e))
        if i < len(AXES) - 1:
            time.sleep(1.05)
    log = read_log_tail()
    latest = {}
    for line in log.splitlines():
        m = re.search(r"slave=(\d+),index=(\d+),subIndex=(\d+),value=(-?\d+)", line)
        if m:
            latest[(int(m.group(1)), int(m.group(2)), int(m.group(3)))] = int(m.group(4))
    for j in range(1, 7):
        v = latest.get((j + 2, 0x5000, 7))
        if v is None:
            print("J%d: no log line yet" % j)
        else:
            print("J%d: 0x%04X = %s" % (j, v & 0xFFFF, VER.get(v & 0xFFFF, "unknown")))
    if not latest:
        print("--- raw log tail (for debugging) ---")
        print(log[-2000:])


if __name__ == "__main__":
    main()
