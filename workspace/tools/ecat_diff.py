
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
def frame_at(path,t):
    pk=[p for p in read_pcap(path) if len(p[1])==1111]
    return min(pk,key=lambda p:abs(p[0]-t))[1]

def diff(label, path, t_before, t_after, lo, hi, name):
    a=frame_at(path,t_before); b=frame_at(path,t_after)
    changes=[]
    for o in range(lo,hi-3,4):
        va=struct.unpack_from('<i',a,o)[0]; vb=struct.unpack_from('<i',b,o)[0]
        if va!=vb: changes.append((o,va,vb))
    print("=== %s : %s (%d..%d) 变化字段 %d 个 ===" % (label,name,lo,hi,len(changes)))
    for o,va,vb in changes[:40]:
        print("    off=%4d   %12d -> %12d" % (o,va,vb))
    if len(changes)>40: print("    ... 共 %d" % len(changes))
    print()

Z="D:\\mydata\\workspace\\data\\codex_b\\ethercat_pcap\\zero32_calibration.pcap"
C="D:\\mydata\\workspace\\data\\codex_b\\ethercat_pcap\\capture315_ethercat.pcap1"
diff("3.2.d.8", Z, 1790063112.3, 1790063117.0, 46, 486, "RxPDO")
diff("3.2.d.8", Z, 1790063112.3, 1790063117.0, 498, 1060, "TxPDO")
diff("3.1.5.0", C, 1790065870.0, 1790065876.0, 46, 486, "RxPDO")
diff("3.1.5.0", C, 1790065870.0, 1790065876.0, 498, 1060, "TxPDO")
