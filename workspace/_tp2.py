import sys
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
sys.path.insert(0, r"D:\mydata\workspace\tools")
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from libdata_strrefs import Elf, scan
e = Elf()
d = e.d
sites = scan(e)
for va in (0x20f5fc, 0x211be0):
    hits = [hex(a) for (a,v) in sites if v==va]
    print(hex(va), "->", hits[:20])
