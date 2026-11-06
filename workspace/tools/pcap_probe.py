
import struct, sys, collections

def read_pcap(path, limit=None):
    with open(path,'rb') as f:
        gh = f.read(24)
        magic = gh[:4]
        if magic == b'\xd4\xc3\xb2\xa1': endian='<'
        elif magic == b'\xa1\xb2\xc3\xd4': endian='>'
        elif magic == b'\x4d\x3c\xb2\xa1': endian='<'
        elif magic == b'\xa1\xb2\x3c\x4d': endian='>'
        else: raise SystemExit('unknown magic %r' % magic)
        linktype = struct.unpack(endian+'I', gh[20:24])[0]
        pkts=[]
        n=0
        while True:
            h=f.read(16)
            if len(h)<16: break
            ts,tu,cap,orig=struct.unpack(endian+'IIII',h)
            data=f.read(cap)
            if len(data)<cap: break
            pkts.append((ts+tu/1e6, data))
            n+=1
            if limit and n>=limit: break
        return endian, linktype, pkts

path=sys.argv[1]
offsets=[int(x) for x in sys.argv[2:]]
endian, linktype, pkts = read_pcap(path, limit=400000)
print("file=%s" % path)
print("endian=%s linktype=%d packets=%d" % (endian, linktype, len(pkts)))
if not pkts: raise SystemExit
print("first_ts=%.3f last_ts=%.3f" % (pkts[0][0], pkts[-1][0]))
lens=collections.Counter(len(d) for _,d in pkts)
print("len histogram top8:", lens.most_common(8))
print("ETH head:", pkts[0][1][:20].hex())
et=collections.Counter()
for _,d in pkts[:20000]:
    if len(d)>=14: et[d[12:14].hex()]+=1
print("ethertype top6:", et.most_common(6))

if offsets:
    print("--- offsets scan on frames len in [1090,1130] ---")
    tuples=collections.Counter()
    for ts,d in pkts:
        if 1090 <= len(d) <= 1130:
            try:
                v=tuple(struct.unpack_from('<i', d, o)[0] for o in offsets)
            except Exception:
                continue
            tuples[v]+=1
    print("distinct tuples: %d" % len(tuples))
    for t,c in tuples.most_common(10):
        print("  %s  x%d" % (list(t), c))
