
import re
d = open(r"D:\mydata\workspace\libdataSvr.so.bin",'rb').read()
pats = (b'/dev/shm', b'shm', b'Shm', b'SHM', b'mmap', b'/tmp/', b'ServoParam', b'servoParam', b'SDO', b'Sdo')
seen=set()
for m in re.finditer(rb'[\x20-\x7e]{4,90}', d):
    s=m.group()
    if any(p in s for p in pats):
        t=s.decode('latin-1')
        if t in seen: continue
        seen.add(t)
        if len(seen)<=45:
            print("  0x%08x  %s" % (m.start(), t))
print("...共 %d 条" % len(seen))
