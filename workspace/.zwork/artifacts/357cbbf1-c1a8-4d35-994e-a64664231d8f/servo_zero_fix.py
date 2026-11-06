#!/usr/bin/env python3
"""servo_zero_fix.py -- make a Dobot CR5 keep its zero on DS.3.1.5.0 servo firmware,
by a controller-side edit only (no servo firmware change at all).

BACKGROUND (established 2026-09-24, see SERVO_SUMMARY.md sections 16-19)
-----------------------------------------------------------------------
* The master's reported joint angle of axis N is
      angle = -(the LAST 32-bit entry of that axis's TxPDO block) * 360/(20000*101)
  The index of that last entry is whatever the master itself wrote into the
  drive's 0x1A00; out of the box it is 0x6062.
* On DS.3.1.5.0 the drive's 0x6062 carries the RAW absolute encoder count as
  soon as the axis is enabled (while disabled it is the re-based value), so the
  reported angle jumps to the raw count (tens of degrees) after every enable.
  On DS.3.2.D.8 the same object stays re-based in both states, which is why
  upgrading the servos "fixed" it.
* 0x6064 carries the RE-BASED value in BOTH enable states on BOTH firmwares.
* The per-slave TxPDO tables are compiled into the PLC application
  (e.g. /dobot/userdata/codesys/allST/Application.app) as plain little-endian
  records:   u16 0 | u32 (subindex<<16 | index) | u32 bit length
  Six tables in slave order 3..8 with entry counts 20/20/20/29/23/24, whose byte
  sizes reproduce the measured wire blocks 57/57/57/93/69/71 exactly.
  Every one of the six tables ends with 0x6062 and has 0x6064 at position 2.
* FIX: swap those two objects in a table.  Both are 32-bit, so the table size -
  and therefore every later offset in the process image - is unchanged.  After
  the swap the last entry is 0x6064, i.e. the re-based value, on 3.1.5.0 too.
  That is a TWO BYTE edit per axis (0x6064 and 0x6062 differ only in the low
  byte), plus a recomputation of Application.crc (CODESYS wrapper holding
  CRC32(app) little-endian at offset 4).
* FIELD-PROVEN 2026-09-24 on slave 8 / J6: after the patch + reboot the master
  wrote 1A00.24 = 0x60640020 for slave 8, the reported angle went from
  20.504629 deg to +0.000356 deg, and it survived a full power cycle.

USAGE
-----
  # 1) look at a local copy of the running application
  python tools/servo_zero_fix.py inspect data/cabinet/Application_live.app

  # 2) patch it (dry run by default; --write to produce files)
  python tools/servo_zero_fix.py patch data/cabinet/Application_live.app \
         --out data/cabinet/Application_fixed.app \
         --crc-out data/cabinet/Application_fixed.crc --write
         #  --slaves all      (default) -> all six servo tables 3..8
         #  --slaves 8        -> only slave 8
         #  --slaves 3,4,5,6,7,8

  # 3) install on the controller (backs up the live variant first), then reboot
  python tools/servo_zero_fix.py install data/cabinet/Application_fixed.app \
         data/cabinet/Application_fixed.crc

  # 4) field verdict (read-only): angles, per-axis firmware, mapping state
  python tools/servo_zero_fix.py check

  # rollback any time
  python tools/servo_zero_fix.py rollback

Everything is reversible: install keeps the originals in a timestamped backup
directory, and rollback restores from it.

NOTE: an engineering download / full-machine upgrade will overwrite the patched
application - re-run steps 2-4 afterwards.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import time
import urllib.request
import zlib
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REC = 10                       # u16 pad, u32 index word, u32 bit length
NAME_TS = b"transmit pdo1"
COUNT_EXPECT = [20, 20, 20, 29, 23, 24]
SLAVE_OF_TABLE = [3, 4, 5, 6, 7, 8]
AXIS_OF_SLAVE = {3: "J1", 4: "J2", 5: "J3", 6: "J4", 7: "J5", 8: "J6"}
VERSION = {0x32D8: "3.2.D.8", 0x3150: "3.1.5.0"}
CTRL_IP = "192.168.5.1"
SCALE = 360.0 / (20000 * 101)          # deg per encoder count
POS_OBJ = 0x6064                        # re-based in both states, both firmwares
BAD_OBJ = 0x6062                        # raw count while enabled on 3.1.5.0
DEFAULT_VARIANT = "/dobot/userdata/codesys/allST/"
LIVE_DIR = "/home/ftp/PlcLogic/Application"
BACKUP_PREFIX = "/dobot/userdata/codesys/BACKUP_pdo_"


# --------------------------------------------------------------------------
# offline: parse / patch / verify
# --------------------------------------------------------------------------
def find_tables(d):
    out = []
    s = 0
    while True:
        i = d.find(NAME_TS, s)
        if i < 0:
            break
        cnt = struct.unpack_from("<H", d, i - 12)[0]
        q = None
        for skip in range(0, 300):
            p = i + len(NAME_TS) + skip
            if p + 8 > len(d):
                break
            word, bits = struct.unpack_from("<II", d, p)
            if word == 0x6041 and bits == 16:
                q = p
                break
        out.append((i, cnt, q))
        s = i + 1
    return out


def parse(d, q, n, base=None):
    """-> list of dicts with index/subindex/bits and the absolute offset of the
    4-byte index word (base lets the caller work on a bytearray)."""
    res = []
    for k in range(n):
        off = q + k * REC
        word, bits = struct.unpack_from("<II", d, off)
        res.append(dict(index=word & 0xFFFF, sub=word >> 16, bits=bits,
                        off=off))
    return res


def crc_blob(app_bytes):
    return (bytes.fromhex("b11a9000")
            + struct.pack("<I", zlib.crc32(app_bytes) & 0xFFFFFFFF)
            + b"Application\x00" + bytes.fromhex("b21a8400")
            + struct.pack("<I", 1))


def load_tables(path):
    orig = open(path, "rb").read()
    d = bytearray(orig)
    tabs = find_tables(d)
    if len(tabs) != 6:
        raise SystemExit("!! expected 6 transmit-PDO tables, found %d - STOP"
                         % len(tabs))
    if [t[1] for t in tabs] != COUNT_EXPECT:
        raise SystemExit("!! entry counts %s != expected %s - STOP"
                         % ([t[1] for t in tabs], COUNT_EXPECT))
    if any(t[2] is None for t in tabs):
        raise SystemExit("!! could not locate an entry block - STOP")
    parsed = [parse(d, q, c) for _, c, q in tabs]
    # control: table sizes must reproduce the measured wire blocks
    sizes = [sum(e["bits"] // 8 for e in ents) for ents in parsed]
    if sizes != [57, 57, 57, 93, 69, 71]:
        raise SystemExit("!! table byte sizes %s != 57/57/57/93/69/71 - STOP"
                         % sizes)
    return orig, d, tabs, parsed, sizes


def cmd_inspect(args):
    orig, d, tabs, parsed, sizes = load_tables(args.app)
    print("app : %s" % args.app)
    print("      %d bytes  md5=%s" % (len(orig), hashlib.md5(orig).hexdigest()))
    print("      six transmit-PDO tables, byte sizes %s == the measured wire "
          "blocks" % sizes)
    print()
    for k, ((ti, cnt, tq), ents) in enumerate(zip(tabs, parsed)):
        slave = SLAVE_OF_TABLE[k]
        first64 = [e for e in ents if e["index"] == POS_OBJ]
        last = ents[-1]
        if last["index"] == POS_OBJ:
            state = "PATCHED  (last entry = 0x6064)"
        elif last["index"] == BAD_OBJ:
            state = "stock    (last entry = 0x6062)"
        else:
            state = "UNKNOWN  (last entry = 0x%04X)" % last["index"]
        print("table %d  slave %d / %s  %2d entries  last=0x%04X:%02X %dbit  "
              "0x6064 at %d  ->  %s"
              % (k, slave, AXIS_OF_SLAVE[slave], cnt, last["index"], last["sub"],
                 last["bits"],
                 first64[0]["off"] - tq if first64 else -1, state))
    print()
    print("index-word offsets to be edited (absolute in the file):")
    for k, ((ti, cnt, tq), ents) in enumerate(zip(tabs, parsed)):
        last = ents[-1]
        if last["index"] != BAD_OBJ:
            continue
        p64 = [e for e in ents if e["index"] == POS_OBJ]
        if not p64:
            continue
        print("   slave %d / %s : 0x%x (0x6064->0x6062) and 0x%x (last, "
              "0x6062->0x6064)" % (SLAVE_OF_TABLE[k], AXIS_OF_SLAVE[SLAVE_OF_TABLE[k]],
                                   p64[0]["off"], last["off"]))
    return 0


def cmd_patch(args):
    orig, d, tabs, parsed, sizes = load_tables(args.app)
    if args.slaves.strip().lower() == "all":
        want = set(SLAVE_OF_TABLE)
    else:
        want = set(int(x) for x in args.slaves.split(",") if x.strip())
    bad = want - set(SLAVE_OF_TABLE)
    if bad:
        raise SystemExit("!! unknown slave number(s) %s (valid: %s)"
                         % (sorted(bad), SLAVE_OF_TABLE))
    print("app : %s  %d bytes  md5=%s"
          % (args.app, len(orig), hashlib.md5(orig).hexdigest()))
    print("tables to fix: %s" % ", ".join("%d/%s" % (s, AXIS_OF_SLAVE[s])
                                          for s in sorted(want)))
    print()
    changed = []
    already = []
    for k, ((ti, cnt, tq), ents) in enumerate(zip(tabs, parsed)):
        slave = SLAVE_OF_TABLE[k]
        if slave not in want:
            continue
        last = ents[-1]
        if last["index"] == POS_OBJ:
            already.append((slave, last))
            print("  slave %d / %s : already patched - skipped"
                  % (slave, AXIS_OF_SLAVE[slave]))
            continue
        if last["index"] != BAD_OBJ:
            raise SystemExit("  !! slave %d / %s has last entry 0x%04X, neither "
                             "0x6064 nor 0x6062 - STOP"
                             % (slave, AXIS_OF_SLAVE[slave], last["index"]))
        p64 = [e for e in ents if e["index"] == POS_OBJ]
        if len(p64) != 1:
            raise SystemExit("  !! slave %d / %s : %d records with 0x6064 - STOP"
                             % (slave, AXIS_OF_SLAVE[slave], len(p64)))
        p64 = p64[0]
        if p64["bits"] != 32 or last["bits"] != 32:
            raise SystemExit("  !! slave %d: both objects must be 32-bit "
                             "(got %d / %d) - STOP"
                             % (slave, p64["bits"], last["bits"]))
        o64, o62 = p64["off"], last["off"]
        if bytes(d[o64:o64 + 4]) != struct.pack("<I", POS_OBJ):
            raise SystemExit("  !! offset check failed at 0x%x - STOP" % o64)
        if bytes(d[o62:o62 + 4]) != struct.pack("<I", BAD_OBJ):
            raise SystemExit("  !! offset check failed at 0x%x - STOP" % o62)
        struct.pack_into("<I", d, o64, BAD_OBJ)
        struct.pack_into("<I", d, o62, POS_OBJ)
        changed += [o64, o62]
        print("  slave %d / %s : 0x%x  0x6064->0x6062   |   0x%x  last "
              "0x6062->0x6064" % (slave, AXIS_OF_SLAVE[slave], o64, o62))

    if not changed:
        print()
        print("nothing to do - every requested axis is already patched")
        return 0

    diff = [i for i in range(len(d)) if d[i] != orig[i]]
    print()
    print("bytes changed: %d  at %s"
          % (len(diff), ", ".join("0x%x" % x for x in diff)))
    # 0x6064 and 0x6062 differ only in their low byte, so each swapped record
    # pair touches exactly one byte per record => len(diff) == len(changed)
    if len(diff) != len(changed):
        raise SystemExit("!! expected %d changed bytes, got %d - STOP"
                         % (len(changed), len(diff)))
    for off in changed:
        if orig[off] not in (0x62, 0x64) or d[off] not in (0x62, 0x64):
            raise SystemExit("!! unexpected byte change at 0x%x - STOP" % off)
    if len(d) != len(orig):
        raise SystemExit("!! file size changed - STOP")

    # gate: reparse and assert the intended outcome
    after = [parse(d, q, c) for _, c, q in tabs]
    for k, ((ti, cnt, tq), ents) in enumerate(zip(tabs, after)):
        slave = SLAVE_OF_TABLE[k]
        if slave in want:
            assert ents[-1]["index"] == POS_OBJ, "slave %d last entry" % slave
        else:
            assert ents == parsed[k], "slave %d changed but was not requested" % slave
    sizes2 = [sum(e["bits"] // 8 for e in ents) for ents in after]
    assert sizes2 == sizes, "sizes changed"
    print("GATE PASS: every requested table now ends with 0x6064 (32 bit); "
          "untouched tables are byte-identical; all sizes unchanged")

    blob = crc_blob(bytes(d))
    print("new Application.crc = %s  (CRC32 = %08x)"
          % (blob.hex(), zlib.crc32(bytes(d)) & 0xFFFFFFFF))

    if not args.write:
        print()
        print("DRY RUN - nothing written (pass --write)")
        return 0
    if not args.out:
        raise SystemExit("--out is required with --write")
    open(args.out, "wb").write(bytes(d))
    print("wrote %s (md5=%s)" % (args.out, hashlib.md5(bytes(d)).hexdigest()))
    if args.crc_out:
        open(args.crc_out, "wb").write(blob)
        print("wrote %s" % args.crc_out)
    return 0


# --------------------------------------------------------------------------
# field plumbing (SSH/SCP: paramiko first, rrun.cmd/rscp.cmd as fallback)
#
# 2026-09-24: the Windows OpenSSH client on this host is broken (every
# invocation of ssh.exe exits rc=255 with zero output, including `ssh -V`),
# which made every ssh_script()-backed section of `check` silently empty.
# Prefer paramiko (pip-installed) and keep the cmd wrappers as fallback.
# The password is parsed at runtime from the workspace's existing
# .askpass.cmd credential file - nothing new is stored here.
# --------------------------------------------------------------------------
def _have_paramiko():
    try:
        import paramiko  # noqa: F401
        return True
    except ImportError:
        return False


def _askpass_password():
    """Reuse the credential already stored in .askpass.cmd (same one the
    rrun.cmd/rscp.cmd wrappers feed to SSH_ASKPASS)."""
    path = os.path.join(ROOT, ".askpass.cmd")
    try:
        with open(path, "r", encoding="ascii", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line.lower().startswith("@echo"):
                    return line.split(None, 1)[1].strip()
    except OSError:
        pass
    raise SystemExit("!! cannot read %s (existing workspace credential file)" % path)


def _paramiko_client():
    import paramiko
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(CTRL_IP, username="root", password=_askpass_password(),
                timeout=15, allow_agent=False, look_for_keys=False)
    return cli


def _run(cmdline):
    p = subprocess.run(cmdline, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def ssh_script(text, label="script"):
    """Run a /bin/sh script on the controller (LF endings, ASCII)."""
    script = text if text.endswith("\n") else text + "\n"
    if _have_paramiko():
        cli = _paramiko_client()
        try:
            stdin, stdout, stderr = cli.exec_command("sh -s", timeout=120)
            stdin.write(script)
            stdin.channel.shutdown_write()
            out = stdout.read().decode("utf-8", "replace")
            err = stderr.read().decode("utf-8", "replace")
            rc = stdout.channel.recv_exit_status()
            return rc, out + (("--- stderr ---\n" + err) if err else "")
        finally:
            cli.close()
    tmp = os.path.join(ROOT, "_tmp_%s.sh" % label)
    with open(tmp, "w", newline="\n", encoding="ascii") as f:
        f.write(script)
    try:
        rc, out = _run(["cmd", "/c", "rrun.cmd", "_tmp_%s.sh" % label])
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    return rc, out


def _sftp_transfer(method, a, b):
    cli = _paramiko_client()
    try:
        sftp = cli.open_sftp()
        getattr(sftp, method)(a, b)
        sftp.close()
        return 0, "%s %s -> %s ok" % (method, a, b)
    except Exception as e:
        return 1, "%s failed: %s" % (method, e)
    finally:
        cli.close()


def scp_put(local, remote, label="put"):
    if _have_paramiko():
        return _sftp_transfer("put", local, remote)
    return _run(["cmd", "/c", "rscp.cmd", local, "root@%s:%s" % (CTRL_IP, remote)])


def scp_get(remote, local):
    if _have_paramiko():
        return _sftp_transfer("get", remote, local)
    return _run(["cmd", "/c", "rscp.cmd", "root@%s:%s" % (CTRL_IP, remote), local])


def variant_dir():
    rc, out = ssh_script("cat /tmp/codesysBoot 2>/dev/null", "boot")
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("/") and line.endswith("/"):
            return line
    return DEFAULT_VARIANT


def cmd_pull(args):
    """Copy the live application out of the controller for offline inspection."""
    rc, out = ssh_script("md5sum %s/Application.app\ncat /proc/uptime" % LIVE_DIR,
                         "pull")
    print(out.strip())
    r1 = scp_get("%s/Application.app" % LIVE_DIR, args.out)
    r2 = scp_get("%s/Application.crc" % LIVE_DIR,
                 args.out[:-4] + ".crc" if args.out.endswith(".app") else args.out + ".crc")
    print("pulled %s" % args.out)
    return 0


def cmd_install(args):
    v = variant_dir()
    print("live variant directory (from /tmp/codesysBoot): %s" % v)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bk = BACKUP_PREFIX + stamp
    script = """#!/bin/sh
BK=%s
V=%s
mkdir -p "$BK"
cp -a $V/Application.app "$BK/Application.app.orig" || exit 1
cp -a $V/Application.crc "$BK/Application.crc.orig" || exit 1
cp -a %s/Application.app "$BK/PlcLogic_Application.app.orig" 2>/dev/null
cp -a %s/Application.crc "$BK/PlcLogic_Application.crc.orig" 2>/dev/null
echo "backed up to $BK"
md5sum "$BK"/*.orig
""" % (bk, v, LIVE_DIR, LIVE_DIR)
    rc, out = ssh_script(script, "install")
    print(out.strip())
    if rc != 0:
        raise SystemExit("!! backup failed - STOP (nothing installed)")

    print()
    print("uploading patched application ...")
    for local, name in ((args.app, "Application.app"), (args.crc, "Application.crc")):
        if not local or not os.path.exists(local):
            raise SystemExit("!! %s missing" % local)
        r = scp_put(local, v + name)
        print("   -> %s%s   rc=%d" % (v, name, r[0]))

    print()
    rc, out = ssh_script(
        "md5sum %s/Application.app\nod -An -tx1 %s/Application.crc\n"
        "echo '--- codesysBoot ---'\ncat /tmp/codesysBoot\n" % (v, v), "verify")
    print(out.strip())
    print()
    print("INSTALLED.  Reboot the controller for it to take effect, then run:")
    print("    python tools/servo_zero_fix.py check")
    print("rollback directory: %s" % bk)
    return 0


def cmd_rollback(args):
    rc, out = ssh_script(
        "ls -d %s* 2>/dev/null | sort | tail -n 1" % BACKUP_PREFIX, "rb")
    bk = out.strip().splitlines()[-1] if out.strip() else ""
    if not bk or not bk.startswith(BACKUP_PREFIX):
        raise SystemExit("!! no backup directory found under %s*" % BACKUP_PREFIX)
    if not args.yes:
        print("will restore from %s" % bk)
        print("re-run with --yes to actually do it")
        return 0
    v = variant_dir()
    script = """#!/bin/sh
BK=%s
V=%s
cp -a "$BK/Application.app.orig" $V/Application.app || exit 1
cp -a "$BK/Application.crc.orig" $V/Application.crc || exit 1
echo "restored to $V"
md5sum $V/Application.app $V/Application.crc
""" % (bk, v)
    rc, out = ssh_script(script, "rollback")
    print(out.strip())
    print()
    print("RESTORED from %s.  Reboot the controller to take effect." % bk)
    return 0


# --------------------------------------------------------------------------
# field verdict (read-only)
# --------------------------------------------------------------------------
def sdo_read(slave_key, index, sub=0):
    body = json.dumps({"body": [{"key": "addr%04X%02X" % (index, sub),
                                 "servoNum": slave_key, "value": 0}]}).encode()
    req = urllib.request.Request(
        "http://%s:22000/settings/readServoParams" % CTRL_IP, data=body,
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=8).read()
    # the value only exists in the controller log - see read_log_tail()
    return None


def read_log_tail():
    """Last SDO result per (slave, index, subindex) - the log is append-only and
    holds every boot, so only the newest occurrence is meaningful."""
    rc, out = ssh_script(
        "L=/dobot/userdata/CR5_sys_files/project/logs/all/log\n"
        "grep -a 'readSDO#4624' $L\n", "log")
    latest = {}
    for line in out.splitlines():
        m = re.search(r"slave=(\d+),index=(\d+),subIndex=(\d+),value=(-?\d+)",
                      line)
        if m:
            latest[(int(m.group(1)), int(m.group(2)), int(m.group(3)))] = \
                int(m.group(4))
    return [(k[0], k[1], k[2], v) for k, v in latest.items()]


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


def mapping_state():
    """Parse the controller's EtherCAT log for the 0x1A00 writes of THIS boot."""
    rc, out = ssh_script(
        "L=/dobot/userdata/CR5_sys_files/project/logs/codesys/log\n"
        "grep -ao 'SDO write ok: Address: [0-9]* Index: 16#1A00 SubIndex: "
        "[0-9]* Data: 16#[0-9A-F]*' $L\n", "map")
    per = {}
    order = []
    for line in out.splitlines():
        m = re.search(r"Address: (\d+) Index: 16#1A00 SubIndex: (\d+) Data: "
                      r"16#([0-9A-F]+)", line)
        if not m:
            continue
        a, sub, data = int(m.group(1)), int(m.group(2)), m.group(3)
        if a not in per:
            per[a] = {}
            order.append(a)
        per[a][sub] = data
    return per, order


def cmd_check(args):
    print("=" * 74)
    print("1) reported joint angles (TCP 30005)")
    print("=" * 74)
    a = joint_values()
    for i in range(6):
        print("   J%d = %+12.6f deg   = %+10.1f counts"
              % (i + 1, a[i], a[i] / SCALE))
    print()

    print("=" * 74)
    print("2) per-axis servo firmware (SDO 0x5000:07 = version word)")
    print("=" * 74)
    for slave in SLAVE_OF_TABLE:
        sdo_read(AXIS_OF_SLAVE[slave], 0x5000, 7)
        time.sleep(1.05)
    for slave, index, sub, val in read_log_tail():
        if index == 0x5000 and sub == 7:
            print("   slave %d / %s : 0x%04X = %s"
                  % (slave, AXIS_OF_SLAVE.get(slave, "?"), val,
                     VERSION.get(val, "unknown")))
    print()

    print("=" * 74)
    print("3) what the master mapped into 0x1A00 this boot "
          "(last entry decides the reported angle)")
    print("=" * 74)
    per, order = mapping_state()
    ok = True
    for a_addr in sorted(per):
        subs = per[a_addr]
        ent3 = subs.get(3)
        n = subs.get(0)
        last = None
        if n is not None:
            last = subs.get(int(n, 16))
        slave = None
        for k, s in enumerate(SLAVE_OF_TABLE):
            if a_addr in (1000 + s, s):
                slave = s
        name = AXIS_OF_SLAVE.get(slave, "?") if slave else "?"
        good = (last == "60640020")
        if not good:
            ok = False
        print("   address %-5d %-3s entries=%-4s entry3=%-10s last=%-10s  %s"
              % (a_addr, name, n, ent3, last,
                 "OK (0x6064 = re-based)" if good
                 else "NOT PATCHED (0x6062 = raw when enabled on 3.1.5.0)"))
    print()
    print("=" * 74)
    print("VERDICT: %s" % ("all servo axes read the re-based object 0x6064 -> "
                           "zero should hold" if ok and per
                           else "see above; re-run 'patch' + 'install' + reboot"))
    print("=" * 74)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("inspect", help="show the six TxPDO tables of an app")
    p.add_argument("app")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("patch", help="swap 0x6064/0x6062 in the selected tables")
    p.add_argument("app")
    p.add_argument("--slaves", default="all")
    p.add_argument("--out")
    p.add_argument("--crc-out")
    p.add_argument("--write", action="store_true")
    p.set_defaults(func=cmd_patch)

    p = sub.add_parser("pull", help="copy the live application off the controller")
    p.add_argument("--out", default=os.path.join("data", "cabinet",
                                                 "Application_live.app"))
    p.set_defaults(func=cmd_pull)

    p = sub.add_parser("install", help="back up + upload the patched application")
    p.add_argument("app")
    p.add_argument("crc")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("rollback", help="restore the newest backup")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_rollback)

    p = sub.add_parser("check", help="read-only field verdict")
    p.set_defaults(func=cmd_check)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
