
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
path=sys.argv[1]; offs=[int(x) for x in sys.argv[2].split(',')]
tgt=tuple(int(x) for x in sys.argv[3].split(','))
pkts=[p for p in read_pcap(path) if len(p[1])==1111]
hit=None
for ts,d in pkts:
    v=tuple(struct.unpack_from('<i',d,o)[0] for o in offs)
    if v==tgt: hit=(ts,d); break
ts,d=hit
print("frame @ %.3f  len=%d" % (ts,len(d)))
print("TxPDO 区 (498..1059) 原始 hex，* 标出 6 个值的位置：")
lo,hi=560,1000
for base in range(lo,hi,16):
    hexs=' '.join('%02x'%b for b in d[base:base+16])
    marks=''.join('*' if (base+i) in offs else ('^' if (base+i-1) in offs or (base+i-2) in offs or (base+i-3) in offs else ' ') for i in range(16))
    print("  %4d  %-47s  %s" % (base, hexs, marks))
print()
print("每个值处的 4 字节窗口（按 值 的字节对齐）：")
for o in offs:
    v=struct.unpack_from('<i',d,o)[0]
    print("  off=%4d  int32=%-10d  bytes@%d = %s" % (o, v, o, ' '.join('%02x'%b for b in d[o:o+4])))
