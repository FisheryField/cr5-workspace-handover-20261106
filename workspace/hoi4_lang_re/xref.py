#!/usr/bin/env python3
"""Find code xrefs (RIP-relative) and data pointers to given strings/addresses."""
import sys, struct
sys.path.insert(0, r"D:\mydata\workspace\hoi4_lang_re")
from pe import PE, EXE, scan_ripxrefs

pe = PE(EXE)

def va_of_str(s, nth=0):
    nb = s.encode()
    start = 0
    c = 0
    while True:
        i = pe.data.find(nb, start)
        if i < 0:
            return None
        if c == nth:
            return pe.off2va(i)
        c += 1
        start = i + 1

def data_ptrs(va, limit=40):
    out = []
    pat = struct.pack('<Q', va)
    start = 0
    while len(out) < limit:
        i = pe.data.find(pat, start)
        if i < 0:
            break
        start = i + 1
        out.append(pe.off2va(i))
    return out

def report(label, va):
    print('### %s  VA=%#010x' % (label, va))
    dptr = data_ptrs(va)
    if dptr:
        print('  数据指针引用 (%d): %s' % (len(dptr), ' '.join('%#x' % x for x in dptr[:20])))
        # also xref the pointers themselves
        extra = {}
        for p in dptr[:20]:
            extra[p] = 'ptr->' + label
        hits = scan_ripxrefs(pe, extra)
        for h in hits:
            print('    代码 xref->指针 %#010x (kind %s)' % (h[0], h[3]))
    hits = scan_ripxrefs(pe, {va: label})
    print('  代码 RIP 相对引用 (%d):' % len(hits))
    for h in hits:
        print('     %#010x  pat=%s' % (h[0], h[3]))
    print()
    return [h[0] for h in hits]

if __name__ == '__main__':
    for arg in sys.argv[1:]:
        if arg.startswith('0x'):
            report(arg, int(arg, 16))
        else:
            parts = arg.split('@')
            va = va_of_str(parts[0], int(parts[1]) if len(parts) > 1 else 0)
            if va is None:
                print('### %s : 未找到' % arg)
            else:
                report(arg, va)
