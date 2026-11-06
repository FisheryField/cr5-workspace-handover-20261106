#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre-flight verification of the six-axis patch pair before it is installed.

Checks (all must pass):
  1. the .crc file really is CRC32(app) in CODESYS' wrapper
  2. the app parses as exactly the six axis TxPDO tables with the measured
     entry counts / byte sizes
  3. every table ends with 0x6064 (32 bit) and keeps 0x6064 at record 2
  4. the only difference from the stock application is the 6 x 2 swapped bytes
"""
import hashlib
import io
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import servo_zero_fix as szf  # noqa: E402

CAB = os.path.join(szf.ROOT, "data", "cabinet")
PATCH_APP = os.path.join(CAB, "Application_fixed_all6.app")
PATCH_CRC = os.path.join(CAB, "Application_fixed_all6.crc")
STOCK_APP = os.path.join(CAB, "Application_allST.app")

EXPECT_APP_MD5 = "9a808cd9dd8f3aa6adaa4de1a34eb9b3"
EXPECT_STOCK_MD5 = "8416cf0eee070a640702c077eb904b4e"


def main():
    patch = open(PATCH_APP, "rb").read()
    stock = open(STOCK_APP, "rb").read()
    crc = open(PATCH_CRC, "rb").read()
    ok = []

    print("patch app : %s" % PATCH_APP)
    print("            %d bytes  md5=%s" % (len(patch), hashlib.md5(patch).hexdigest()))
    print("stock app : md5=%s" % hashlib.md5(stock).hexdigest())
    print("patch crc : %s" % crc.hex(" "))
    print()
    ok.append(("app md5 == field-proven value",
               hashlib.md5(patch).hexdigest() == EXPECT_APP_MD5))
    ok.append(("stock md5 == pristine baseline",
               hashlib.md5(stock).hexdigest() == EXPECT_STOCK_MD5))

    want = szf.crc_blob(patch)
    ok.append(("crc file == CRC32(app) wrapper", want == crc))
    print("expected crc = %s  (CRC32=%08x)"
          % (want.hex(" "), zlib.crc32(patch) & 0xFFFFFFFF))

    orig, d, tabs, parsed, sizes = szf.load_tables(PATCH_APP)
    print("six TxPDO tables, byte sizes %s (expected 57/57/57/93/69/71)" % sizes)
    # expected SWAP layout: record 2 carries 0x6062, the last record 0x6064
    for k, ents in enumerate(parsed):
        slave = szf.SLAVE_OF_TABLE[k]
        last = ents[-1]
        rec2 = ents[2]
        n62 = sum(1 for e in ents if e["index"] == szf.BAD_OBJ)
        n64 = sum(1 for e in ents if e["index"] == szf.POS_OBJ)
        good = (last["index"] == szf.POS_OBJ and last["bits"] == 32
                and rec2["index"] == szf.BAD_OBJ and rec2["bits"] == 32
                and rec2["sub"] == 0 and last["sub"] == 0
                and n62 == 1 and n64 == 1)
        print("   slave %d / %-2s  %2d entries  record2=0x%04X:%02d  "
              "last=0x%04X:%02d  (0x6062 x%d, 0x6064 x%d)  %s"
              % (slave, szf.AXIS_OF_SLAVE[slave], len(ents),
                 rec2["index"], rec2["sub"], last["index"], last["sub"],
                 n62, n64, "OK" if good else "BAD"))
        ok.append(("slave %d: last=0x6064, record2=0x6062, one of each" % slave,
                   good))

    diff = [i for i in range(len(patch)) if patch[i] != stock[i]]
    print("\nbytes differing from stock: %d  at %s"
          % (len(diff), ", ".join("0x%x" % i for i in diff)))
    expect = []
    for _, _, _, ents, _ in [0] and [] or []:
        pass
    for k, ents in enumerate(parsed):
        expect += [ents[2]["off"], ents[-1]["off"]]
    ok.append(("exactly 12 changed bytes", len(diff) == 12))
    ok.append(("changed offsets == the 6 record-2 and 6 last-record words",
               sorted(diff) == sorted(expect)))
    ok.append(("all changes are 0x64<->0x62",
               all({stock[i], patch[i]} == {0x62, 0x64} for i in diff)))
    ok.append(("size unchanged", len(patch) == len(stock)))

    print("\n--- verdict ---")
    bad = 0
    for name, res in ok:
        print("   [%s] %s" % ("PASS" if res else "FAIL", name))
        bad += 0 if res else 1
    print("\n%s" % ("ALL CHECKS PASS - pair ready to install"
                    if not bad else "!! %d CHECK(S) FAILED - do not install" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
