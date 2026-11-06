
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

# J1 TxPDO 块映射（从 codesys 日志 0x1A00 推出），块起点 = 600
TXMAP=[("0x6041 Statusword",0,2,False),("0x6061 Mode disp",2,1,False),
       ("0x6064 Position actual",3,4,True),("0x606C Velocity actual",7,4,True),
       ("0x6077 Torque actual",11,2,True),("0x6075 Motor rated I",13,4,True),
       ("0x6076 Motor rated T",17,4,True),("0x603F Error code",21,2,False),
       ("0x6079 DC link V",23,4,False),("0x6078 Current actual",27,2,True),
       ("0x5000:02",29,2,True),("0x5000:03",31,2,True),("0x5000:06",33,2,True),
       ("0x5000:07",35,2,True),("0x5000:08",37,2,True),
       ("0x5002:03",39,4,True),("0x5002:04",43,4,True),("0x5002:06",47,2,True),
       ("0x606B Velocity demand",49,4,True),("0x6062 Position demand",53,4,True)]
BLK=600

def dump(label,path,t):
    fr=frame_at(path,t)
    print("=== %s ===" % label)
    raw=fr[BLK:BLK+57]
    print("  raw:", ' '.join('%02x'%b for b in raw[:29]))
    print("       ", ' '.join('%02x'%b for b in raw[29:]))
    for nm,off,ln,sg in TXMAP:
        v=int.from_bytes(fr[BLK+off:BLK+off+ln],'little',signed=sg)
        print("   +%-3d %-24s = %-12d (0x%0*x)" % (off,nm,v,ln*2,v & ((1<<(ln*8))-1)))
    print()

Z="D:\\mydata\\workspace\\data\\codex_b\\ethercat_pcap\\zero32_calibration.pcap"
C="D:\\mydata\\workspace\\data\\codex_b\\ethercat_pcap\\capture315_ethercat.pcap1"
dump("3.2.D.8  标定前 (t=-3.1s)",  Z, 1790063112.3)
dump("3.2.D.8  标定后 (t=+1.5s)",  Z, 1790063116.9)
dump("3.1.5.0  标定前 (t=-4.0s)",  C, 1790065870.0)
dump("3.1.5.0  标定后 (t=+2.0s)",  C, 1790065876.0)
