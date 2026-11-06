#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Variant B of the CR5 zero fix: make the LAST TxPDO entry 0x6064 as well.

Why (2026-09-24, field evidence):

  * The master derives TWO things from each axis's TxPDO block:
      - the reported joint angle  <- the LAST 32-bit entry of the block
      - the axis "actual position" <- the record at entry position 2
    (proved from the PoseTrace log: on 3.1.5.0 axis J6 the last entry was
     0x6062 = 20.501243 deg and the entry-2 value was 0.004099 deg, and the
     log printed exactly nextPos=20.501243 / gActualPosition=0.004099.)
  * libalgs raises alarm 0x86 ("上使能关节位置偏差过大", alarm_controller.json
    id 134) when |reported - actual| exceeds a threshold.  On 3.2.D.8 both
    entries carry the SAME re-based value, so the deviation is identically 0
    and the check never fires.  On 3.1.5.0 entry-2 (0x6062) becomes the raw
    absolute encoder angle once the axis is enabled, so the deviation equals
    |zero base| -- harmless while the base is small (J6: 20.5 deg) but fatal
    once the base is garbage (here: 57..139 deg after re-flashing the servos).

  * Variant A ("swap", tools/servo_zero_fix.py) puts 0x6064 last -> the
    reported angle is correct, but the deviation is UNCHANGED (|a-b| does not
    care which one sits where), so the alarm still fires.
  * Variant B (this script) leaves 0x6064 in its original slot AND makes the
    last entry 0x6064 too, so the input image carries the re-based value
    twice -- exactly what a 3.2.D.8 axis produces.  Reported angle correct
    AND deviation identically 0, so enable + cali home are possible.

  Cost: 1 byte per axis (6 bytes total), size neutral, CRC recomputed.
  Risk: the slave 0x1A00 mapping now names 0x6064 twice and 0x6062 not at
  all; a drive that rejects duplicate mapping entries would fail to reach OP.
  Recovery: tools/servo_zero_fix.py rollback  /  BACKUP_ORIGINAL.
"""
import argparse
import hashlib
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

ROOT = szf.ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("app", nargs="?",
                    default=os.path.join(ROOT, "data", "cabinet",
                                         "Application_allST.app"),
                    help="PRISTINE stock app (default: the BACKUP_ORIGINAL copy)")
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "cabinet",
                                                  "Application_dup6064.app"))
    ap.add_argument("--crc-out", default=os.path.join(ROOT, "data", "cabinet",
                                                      "Application_dup6064.crc"))
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    orig, d, tabs, parsed, sizes = szf.load_tables(args.app)
    print("stock app : %s" % args.app)
    print("            %d bytes  md5=%s" % (len(orig), hashlib.md5(orig).hexdigest()))
    print("            six TxPDO tables, byte sizes %s" % sizes)
    print()

    edits = []
    for k, ents in enumerate(parsed):
        slave = szf.SLAVE_OF_TABLE[k]
        last = ents[-1]
        p64 = [i for i, e in enumerate(ents) if e["index"] == szf.POS_OBJ]
        # --- positive controls on the stock file -------------------------
        if last["index"] != szf.BAD_OBJ or last["bits"] != 32:
            raise SystemExit("!! slave %d: last entry is 0x%04X/%d bit, expected "
                             "0x6062/32 - STOP"
                             % (slave, last["index"], last["bits"]))
        if p64 != [2]:
            raise SystemExit("!! slave %d: 0x6064 sits at record(s) %s, expected "
                             "[2] - STOP" % (slave, p64))
        if bytes(d[last["off"]:last["off"] + 4]) != struct.pack("<I", szf.BAD_OBJ):
            raise SystemExit("!! slave %d: offset check failed at 0x%x - STOP"
                             % (slave, last["off"]))
        edits.append((slave, last["off"]))
        print("  slave %d / %-2s : last record @0x%-7x  0x6062 -> 0x6064 "
              "(record 2 keeps 0x6064)"
              % (slave, szf.AXIS_OF_SLAVE[slave], last["off"]))

    for slave, off in edits:
        struct.pack_into("<I", d, off, szf.POS_OBJ)

    # --- gates -----------------------------------------------------------
    diff = [i for i in range(len(d)) if d[i] != orig[i]]
    if len(diff) != len(edits):
        raise SystemExit("!! %d changed bytes, expected %d - STOP"
                         % (len(diff), len(edits)))
    if any(orig[i] != 0x62 or d[i] != 0x64 for i in diff):
        raise SystemExit("!! an unexpected byte changed - STOP")
    if len(d) != len(orig):
        raise SystemExit("!! file size changed - STOP")
    after = [szf.parse(d, q, c) for _, c, q in tabs]
    for k, ents in enumerate(after):
        slave = szf.SLAVE_OF_TABLE[k]
        got = [e["index"] for e in ents]
        if got[-1] != szf.POS_OBJ:
            raise SystemExit("!! slave %d last entry is 0x%04X - STOP"
                             % (slave, got[-1]))
        if got.count(szf.POS_OBJ) != 2:
            raise SystemExit("!! slave %d has %d x 0x6064, expected 2 - STOP"
                             % (slave, got.count(szf.POS_OBJ)))
        if szf.BAD_OBJ in got:
            raise SystemExit("!! slave %d still maps 0x6062 - STOP" % slave)
        if [e["bits"] for e in ents] != [e["bits"] for e in parsed[k]]:
            raise SystemExit("!! slave %d bit lengths changed - STOP" % slave)
    sizes2 = [sum(e["bits"] // 8 for e in ents) for ents in after]
    if sizes2 != sizes:
        raise SystemExit("!! table byte sizes changed: %s - STOP" % sizes2)
    print()
    print("GATE PASS: 6 single-byte edits (0x62->0x64); every axis table now "
          "carries 0x6064 at record 2 AND at the last record, 0x6062 is gone, "
          "all bit lengths and byte sizes unchanged")
    print("bytes changed: %s" % ", ".join("0x%x" % x for x in diff))

    blob = szf.crc_blob(bytes(d))
    print("new Application.crc = %s  (CRC32 = %08x)"
          % (blob.hex(), zlib.crc32(bytes(d)) & 0xFFFFFFFF))
    if not args.write:
        print()
        print("DRY RUN - nothing written (pass --write)")
        return 0
    open(args.out, "wb").write(bytes(d))
    open(args.crc_out, "wb").write(blob)
    print()
    print("wrote %s (md5=%s)" % (args.out, hashlib.md5(bytes(d)).hexdigest()))
    print("wrote %s" % args.crc_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
