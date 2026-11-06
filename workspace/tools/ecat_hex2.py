
import struct, sys
def read_pcap(path):
    with open(path,'rb') as f:
        gh=f.read(24); net=struct.unpack('<I',gh[20:24])[0]; pkts=[]
        while True:
            h=f.read(16)
            if len(h)<16: break
            ts,tu,cap,orig=struct.unpack('<IIII',h)
            d=f.read(cap)
            if len(d)<cap: break
            if net==276: d=b'\x00'*12+b'\x88\xa4'+d[20:]
            pkts.append((ts+tu/1e6,d))
        return pkts
pk=[p for p in read_pcap(sys.argv[1]) if len(p[1])==1111]
ts,d=min(pk,key=lambda p:abs(p[0]-float(sys.argv[2])))
POS=[603,660,717,810,879,950]
VER=[585,642,699,756,849,920]
print("frame @ %.3f" % ts)
print("   offset  hex                                              P                V")
for base in range(536, 1008, 16):
    hexs=' '.join('%02x'%b for b in d[base:base+16])
    mp=''.join('P' if (base+i) in POS else ' ' for i in range(16))
    mv=''.join('V' if (base+i) in VER else ' ' for i in range(16))
    print("  %4d  %-47s  %-16s %s" % (base, hexs, mp, mv))
