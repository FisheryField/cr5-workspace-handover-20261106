#!/usr/bin/env python3
import sys
sys.path.insert(0, r"D:\mydata\workspace\hoi4_lang_re")
from pe import PE, EXE, scan_ripxrefs
pe = PE(EXE)
for a in sys.argv[1:]:
    va = int(a, 16)
    s = pe.cstr(va, 64)
    print('%#010x : %r' % (va, s))
