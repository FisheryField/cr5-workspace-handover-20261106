#!/usr/bin/env python3
"""Dump null-terminated strings in a VA window, and search needles -> VAs."""
import sys, re
sys.path.insert(0, r"D:\mydata\workspace\hoi4_lang_re")
from pe import PE, EXE

pe = PE(EXE)

def dump(va_start, va_end, minlen=3):
    off = pe.va2off(va_start)
    end = pe.va2off(va_end)
    if off is None or end is None:
        print('  <out of range>')
        return
    blob = pe.data[off:end]
    cur = bytearray()
    cur_va = None
    for i, b in enumerate(blob + b'\0'):
        if 0x20 <= b < 0x7f:
            if cur_va is None:
                cur_va = va_start + i
            cur.append(b)
        else:
            if cur and len(cur) >= minlen:
                print('  %#010x  len=%-3d %s' % (cur_va, len(cur), cur.decode('latin1')))
            cur = bytearray()
            cur_va = None

def search(needle, limit=30):
    nb = needle.encode()
    print('== search %r ==' % needle)
    start = 0
    n = 0
    while n < limit:
        i = pe.data.find(nb, start)
        if i < 0:
            break
        start = i + 1
        n += 1
        va = pe.off2va(i)
        sec = pe.section_of(va)
        pre = pe.data[max(0, i-48):i].decode('latin1').replace('\0', '|')
        post = pe.data[i+len(nb):i+len(nb)+48].decode('latin1').replace('\0', '|')
        print('  off=%#x va=%#010x %-7s  <<%s>>%s' % (i, va, sec['name'] if sec else '?', pre, post))

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'dump':
        dump(int(sys.argv[2], 16), int(sys.argv[3], 16), int(sys.argv[4]) if len(sys.argv) > 4 else 3)
    else:
        for n in sys.argv[1:]:
            search(n)
