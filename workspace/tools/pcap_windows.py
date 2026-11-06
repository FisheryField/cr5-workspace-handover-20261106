
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
path=sys.argv[1]
cuts=[float(x) for x in sys.argv[2].split(',')]
labels=sys.argv[3].split(',')
pkts=read_pcap(path)
print("ts range %.3f .. %.3f  frames=%d" % (pkts[0][0], pkts[-1][0], len(pkts)))
buckets=collections.defaultdict(collections.Counter)
for ts,d in pkts:
    if len(d)<960: continue
    v=tuple(struct.unpack_from('<i',d,o)[0] for o in offs)
    i=0
    while i<len(cuts) and ts>=cuts[i]: i+=1
    buckets[labels[i]][v]+=1
for lab in labels:
    c=buckets[lab]
    tot=sum(c.values())
    print("--- %s : %d frames ---" % (lab, tot))
    for v,n in c.most_common(4):
        print("    %-60s x%d" % (str(list(v)), n))
