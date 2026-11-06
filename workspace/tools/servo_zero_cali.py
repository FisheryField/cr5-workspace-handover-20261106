#!/usr/bin/env python3
"""servo_zero_cali.py -- remote zero-calibration driver for Dobot CR5 (2026-09-25).

Drives the controller's own HTTP channel (port 22000, the exact one
DobotStudio Pro uses), step by step, with full logging:

  preflight (default, read-only):
     joint angles, per-axis SDO 0x6064/0x6062/0x6077/0x6078, alarm state,
     enable state, latest calihome log lines;

  actions (need --go):
     --clear   POST /panel/clearAlarm   (clears servo alarms such as 34322)
     --cali    POST /calibrate/home     (the calibration request itself)
     --verify  read joint angles + homeEncoder.json tail

The 34322 "position out of range" alarm on J1 fires within 150 ms of the
calihome request (seen 11:55 and 14:28 today); clearing it first and doing
cali in the enabled state is the recovery path attempted here.
"""
import argparse
import json
import os
import re
import socket
import struct
import subprocess
import sys
import time
import urllib.request

CTRL_IP = "192.168.5.1"
SCALE = 360.0 / (20000 * 101)
AXES = ["J1", "J2", "J3", "J4", "J5", "J6"]
HERE = os.path.dirname(os.path.abspath(__file__))
LOG_ALL = "/dobot/userdata/CR5_sys_files/project/logs/all/log"
HOMEJSON = "/dobot/userdata/project/settings/function/homeEncoder.json"


def ssh(cmd, timeout=120):
    p = subprocess.run([sys.executable, os.path.join(HERE, "rssh.py"), cmd],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def http(path, body=None, quiet=False):
    url = "http://%s:22000%s" % (CTRL_IP, path)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=10)
        txt = r.read().decode(errors="replace")
    except Exception as e:
        txt = "ERR %s" % e
    if not quiet:
        print("  POST %s -> %s  (%.2fs)" % (path, txt.strip(), time.time() - t0))
    return txt


def log_grep(pattern, tail=12, show=True):
    rc, out = ssh("grep -a '%s' %s | tail -n %d" % (pattern, LOG_ALL, tail))
    if show:
        print((out.strip() or "  (no match)"))
    return out


def joint_values():
    s = socket.create_connection((CTRL_IP, 30005), timeout=6)
    buf = b""
    while len(buf) < 1440:
        chunk = s.recv(4096)
        if not chunk:
            break
        buf += chunk
    s.close()
    v = struct.unpack_from("<180d", buf, 0)
    return [v[(192 + 8 * i) // 8] for i in range(6)]


def show_joints(tag):
    try:
        a = joint_values()
        print("%s:" % tag)
        for i in range(6):
            print("   J%d = %+12.6f deg  (%+10.1f counts)"
                  % (i + 1, a[i], a[i] / SCALE))
        return a
    except Exception as e:
        print("%s: ERR %s" % (tag, e))
        return None


def sdo_batch(tag, index):
    """Fire one SDO read per axis, then grep the newest per-axis values."""
    for ax in AXES:
        http("/settings/readServoParams",
             {"body": [{"key": "addr%04X00" % index, "servoNum": ax, "value": 0}]},
             quiet=True)
        time.sleep(1.05)
    rc, out = ssh("grep -a 'readSDO#4624' %s | tail -n %d"
                  % (LOG_ALL, len(AXES) * 2))
    vals = {}
    for line in out.splitlines():
        m = re.search(r"slave=(\d+),index=(\d+),subIndex=(\d+),value=(-?\d+)", line)
        if m and int(m.group(2)) == index:
            vals["J%d" % (int(m.group(1)) - 2)] = int(m.group(4))
    print("  %-26s 0x%04X :" % (tag, index), end="")
    for ax in AXES:
        v = vals.get(ax, None)
        print("  %s=%s" % (ax, v if v is not None else "?"), end="")
    print()
    return vals


def preflight():
    print("=" * 74)
    print("0) 当前关节角（TCP 30005，只读）")
    print("=" * 74)
    show_joints("  now")
    print()
    print("=" * 74)
    print("1) 驱动器侧（SDO 只读探针，值回日志）")
    print("=" * 74)
    sdo_batch("actual pos  (0x6064)", 0x6064)
    sdo_batch("raw/demand  (0x6062)", 0x6062)
    sdo_batch("min limit   (0x6077)", 0x6077)
    sdo_batch("max limit   (0x6078)", 0x6078)
    print()
    print("=" * 74)
    print("2) 报警/使能状态（日志尾部，只读）")
    print("=" * 74)
    log_grep("logServoError|monitorErrorStatus", 6)
    log_grep("robot enabled|robot disabled", 4)
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true", help="enable actions")
    ap.add_argument("--clear", action="store_true", help="POST /panel/clearAlarm")
    ap.add_argument("--cali", action="store_true", help="POST /calibrate/home")
    ap.add_argument("--verify", action="store_true", help="post-check readback")
    args = ap.parse_args()

    if not args.go:
        preflight()
        return 0

    if args.clear:
        print("\n== clear alarm ==")
        http("/panel/clearAlarm", {})
        time.sleep(2.0)
        log_grep("logServoError|monitorErrorStatus", 6)

    if args.cali:
        print("\n== calibrate ==")
        show_joints("  before")
        http("/calibrate/home", {})
        time.sleep(6.0)
        log_grep("calihome", 16)
        rc, out = ssh("tail -c 400 %s" % HOMEJSON)
        print("  homeEncoder.json tail:\n%s" % out.strip())

    if args.verify:
        print("\n== verify ==")
        show_joints("  after")
        rc, out = ssh("tail -c 400 %s" % HOMEJSON)
        print("  homeEncoder.json tail:\n%s" % out.strip())

    return 0


if __name__ == "__main__":
    sys.exit(main())
