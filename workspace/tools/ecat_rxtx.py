
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
def frame_at(path,t,size=1111):
    pk=[p for p in read_pcap(path) if len(p[1])==size]
    return min(pk,key=lambda p:abs(p[0]-t))
rx=[97,142,187,232,287,334]
tx=[603,660,717,810,879,950]
scale=360/(20000*101)
cases=[
 ("3.2.d.8 标定前一帧", sys.argv[1], float(sys.argv[2])),
 ("3.1.5.0 标定后2.5s", sys.argv[3], float(sys.argv[4])),
 ("3.1.5.0 上使能后/标定前", sys.argv[3], float(sys.argv[5])),
]
for label,path,t in cases:
    ts,fr=frame_at(path,t)
    print("=== %s   @ %.3f ===" % (label, ts))
    print("  RxPDO(主站发出) :", [struct.unpack_from('<i',fr,o)[0] for o in rx])
    print("  TxPDO(从站报回) :", [struct.unpack_from('<i',fr,o)[0] for o in tx])
    r=[struct.unpack_from('<i',fr,o)[0] for o in rx]
    x=[struct.unpack_from('<i',fr,o)[0] for o in tx]
    print("  Rx 是否等于 Tx  :", r==x)
    print("  Tx×scale (度)   :", [round(v*scale,4) for v in x])
    print()
