#!/usr/bin/env python3
"""Find direct call/jmp (E8/E9 rel32) references to target VAs."""
import sys, struct
sys.path.insert(0, r"D:\mydata\workspace\hoi4_lang_re")
from pe import PE, EXE

pe = PE(EXE)
targets = {}
for a in sys.argv[1:]:
    targets[int(a, 16)] = a

for s in pe.sections:
    if not (s['chars'] & 0x20000000):
        continue
    blob = pe.data[s['rawptr']:s['rawptr'] + s['rawsize']]
    base = pe.image_base + s['va']
    for op in (0xE8, 0xE9):
        start = 0
        while True:
            i = blob.find(bytes([op]), start)
            if i < 0:
                break
            start = i + 1
            if i + 5 > len(blob):
                continue
            rel = struct.unpack_from('<i', blob, i + 1)[0]
            tgt = base + i + 5 + rel
            if tgt in targets:
                print('%#010x -> %s' % (base + i, targets[tgt]))
