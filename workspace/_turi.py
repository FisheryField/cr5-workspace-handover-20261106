import sys
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
sys.path.insert(0, r"D:\mydata\workspace\tools")
import re
from libdata_strrefs import Elf, scan
e = Elf()
d = e.d
sites = scan(e)
# Route strings in .rodata: find all "/xxx/yyy" URI-looking strings and where referenced
rd = [s for s in e.secs if s["name"]==".rodata"][0]
blob = d[rd["offset"]:rd["offset"]+rd["size"]]
base = rd["addr"]
uris = []
for m in re.finditer(rb"(?:^|\x00)(/[a-z]+/[a-zA-Z]+)(?:\x00)", blob):
    uris.append((base+m.start(1), m.group(1).decode()))
print("total URIs:", len(uris))
sites_map = {}
for a,v in sites:
    sites_map.setdefault(v, []).append(a)
for va, s in uris:
    hits = sites_map.get(va, [])
    print("%-38s 0x%08x -> %s" % (s, va, [hex(x) for x in hits[:4]]))
