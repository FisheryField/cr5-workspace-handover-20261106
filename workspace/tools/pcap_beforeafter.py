
import struct, sys, collections
def read_pcap(path):
    with open(path,'rb') as f:
        gh=f.read(24)
        endian = '<' if gh[:4] in (b'\xd4\xc3\xb2\xa1', b'\x4d\x3c\xb2\xa1') else '>'
        pkts=[]
        while True:
            h=f.read(16)
            if len(h)<16: break
            ts,tu,cap,orig=struct.unpack(endian+'IIII',h)
            d=f.read(cap)
            if len(d)<cap: break
            pkts.append((ts+tu/1e6,d))
        return pkts

offs=[603,660,717,810,879,950]
path, cut, target = sys.argv[1], float(sys.argv[2]), sys.argv[3]
tgt=tuple(int(x) for x in target.split(','))
pkts=read_pcap(path)
before=after=0
first_before=first_after=None
for ts,d in pkts:
    if len(d)<960: continue
    v=tuple(struct.unpack_from('<i',d,o)[0] for o in offs)
    if v==tgt:
        if ts<cut:
            before+=1
            if first_before is None: first_before=ts
        else:
            after+=1
            if first_after is None: first_after=ts
print("target tuple : %s" % (list(tgt),))
print("cut ts       : %.3f" % cut)
print("occurrences BEFORE cut: %d  (first at %.3f)" % (before, first_before if first_before else -1))
print("occurrences AFTER  cut: %d  (first at %.3f)" % (after, first_after if first_after else -1))
