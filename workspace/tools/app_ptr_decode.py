#!/usr/bin/env python3
"""Decode the .app pointer encoding and validate it against the live image.

Observed model:
  * file pointers are stored as 0x00800000 + file_off - D   (D to be solved)
  * rather: runtime_addr = file_word - 0x00800000 + LOAD_DELTA
  * for the code region we measured LOAD_DELTA = 0x75a95cd0 (file 0x400 <-> 0x75a960d0)
"""
import struct, sys, hashlib

APP = r"D:\mydata\workspace\data\Application.app"
d = open(APP, 'rb').read()
N = len(d)

DUMP = sys.argv[1] if len(sys.argv) > 1 else r"D:\mydata\workspace\data\appmap\reg_75a76000.bin"
DUMP_BASE = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x75a76000
m = open(DUMP, 'rb').read()

LOAD_DELTA = 0x75a95cd0           # runtime = file_off + LOAD_DELTA
BIAS = 0x00800000                 # encoded pointer bias
FILE_BASE = (LOAD_DELTA - BIAS) & 0xffffffff
print("LOAD_DELTA  = 0x%08x" % LOAD_DELTA)
print("implied FILE_BASE = LOAD_DELTA - 0x00800000 = 0x%08x" % FILE_BASE)
print()

# 1) collect all encoded pointers (words whose value >= 0x00800000)
ptrs = []
for i in range(0, N - 4, 4):
    v, = struct.unpack_from("<I", d, i)
    if v >= BIAS:
        ptrs.append((i, v))
print("encoded pointers (word >= 0x00800000): %d" % len(ptrs))

# 2) do they all decode into a plausible file range?
lo, hi = 1 << 30, -1
inside = 0
for i, v in ptrs:
    t = (v - FILE_BASE) & 0xffffffff
    if t < N:
        inside += 1
    lo = min(lo, v)
    hi = max(hi, v)
print("  value range 0x%08x .. 0x%08x" % (lo, hi))
print("  decode inside file: %d / %d" % (inside, len(ptrs)))
print()

# 3) verify a sample against the live dump: for each pointer, the target's file
#    offset should map to the same runtime target
import random
random.seed(7)
sample = random.sample(ptrs, 40)
ok = 0
for i, v in sample:
    tgt_off = (v - FILE_BASE) & 0xffffffff
    if tgt_off >= N:
        continue
    runtime_tgt = (tgt_off + LOAD_DELTA) & 0xffffffff
    # the literal at file offset i should read in the dump (at i+LOAD_DELTA) as
    # the little-endian encoding of runtime_tgt
    dpos = i + LOAD_DELTA - DUMP_BASE
    if dpos < 0 or dpos + 4 > len(m):
        continue
    live = struct.unpack_from("<I", m, dpos)[0]
    if live == runtime_tgt:
        ok += 1
    else:
        print("  MISMATCH file 0x%06x: word 0x%08x -> tgt_off 0x%06x -> expect 0x%08x, live 0x%08x" %
              (i, v, tgt_off, runtime_tgt, live))
print("sample verification: %d/%d pointers decode to the live value at i+LOAD_DELTA" % (ok, len(sample)))
