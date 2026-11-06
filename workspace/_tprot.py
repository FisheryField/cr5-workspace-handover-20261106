import sys
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
sys.path.insert(0, r"D:\mydata\workspace\tools")
import re
from libdata_strrefs import Elf, scan
e = Elf()
d = e.d
# find standalone c-strings exactly "protocol" / "exchange" in .rodata
rd = [s for s in e.secs if s["name"]==".rodata"][0]
blob = d[rd["offset"]:rd["offset"]+rd["size"]]
base = rd["addr"]
for tok in (b"protocol\x00", b"exchange\x00", b"Exchange\x00"):
    for m in re.finditer(re.escape(b"\x00"+tok), blob):
        va = base + m.start()+1
        print(tok, hex(va))
sites = scan(e)
