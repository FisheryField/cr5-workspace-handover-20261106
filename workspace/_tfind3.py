import sys
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
sys.path.insert(0, r"D:\mydata\workspace\tools")
from libdata_strrefs import Elf, scan
e = Elf()
sites = scan(e)
va = 0x214a74  # "clear error from http exchange"
hits = [hex(a) for (a, v) in sites if v == va]
print("code sites:", hits)
# also the "done" variant
va2 = e.d.find(b"clear error from http exchange done")
hits2 = [hex(a) for (a, v) in sites if v == va2]
print("done sites:", hits2)
