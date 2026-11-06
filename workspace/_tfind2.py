import sys
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
sys.path.insert(0, r"D:\mydata\workspace\tools")
import struct
from libdata_strrefs import Elf, scan

e = Elf()
sites = scan(e)
print("sites:", len(sites))
# control: the log string "clear error from http exchange .... " at 0x214a74 (VA == fileoff since .rodata offset==addr? check)
d = e.d
va = d.find(b"clear error from http exchange")
print("string fileoff:", hex(va))
# .rodata addr==offset for this lib (verify)
sec = [s for s in e.secs if s["addr"] and s["addr"] <= va < s["addr"]+s["size"]]
print("section:", [(s["name"], hex(s["addr"]), hex(s["offset"]), hex(s["size"])) for s in sec])
hits = [(a, v) for a, v in sites if v == va]
print("code sites referencing it:", [hex(a) for a in hits])
