
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
def frame_at(path, t, size=1111):
    pk=[p for p in read_pcap(path) if len(p[1])==size]
    return min(pk, key=lambda p: abs(p[0]-t))

vals=[598234,-192592,-580282,389348,-718959,576819]
ts,fr = frame_at(sys.argv[1], float(sys.argv[2]))
print("3.2.d.8 frame @ %.3f len=%d" % (ts,len(fr)))
for i,v in enumerate(vals):
    pat=struct.pack('<i',v)
    hits=[]
    st=0
    while True:
        j=fr.find(pat, st)
        if j<0: break
        hits.append(j); st=j+1
    print("  J%d  %-9d 出现在偏移: %s" % (i+1, v, hits))

print()
print("=== 按 4 字节对齐扫描 (TxPDO 498..1059) 中所有非零 int32 ===")
for o in range(498, 1058, 4):
    v=struct.unpack_from('<i',fr,o)[0]
    if v!=0 and abs(v)>1000:
        print("   %4d = %-12d (0x%08x)" % (o, v, v & 0xFFFFFFFF))
