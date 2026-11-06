
import struct, sys
def read_pcap(path):
    with open(path,'rb') as f:
        f.read(24); pkts=[]
        while True:
            h=f.read(16)
            if len(h)<16: break
            ts,tu,cap,orig=struct.unpack('<IIII',h)
            d=f.read(cap)
            if len(d)<cap: break
            pkts.append((ts+tu/1e6,d))
        return pkts
rx=[97,142,187,232,287,334]
tx=[603,660,717,810,879,950]
path=sys.argv[1]; t0=float(sys.argv[2]); t1=float(sys.argv[3]); step=float(sys.argv[4])
pk=sorted([p for p in read_pcap(path) if len(p[1])==1111])
print("frame count(1111)=%d  span %.3f..%.3f" % (len(pk), pk[0][0], pk[-1][0]))
t=t0
while t<=t1:
    ts,fr=min(pk,key=lambda p:abs(p[0]-t))
    r=[struct.unpack_from('<i',fr,o)[0] for o in rx]
    x=[struct.unpack_from('<i',fr,o)[0] for o in tx]
    print("  t=%+.2f  Rx=%s" % (ts-t0, ' '.join('%8d'%v for v in r)))
    print("             Tx=%s" % (' '.join('%8d'%v for v in x)))
    t+=step
