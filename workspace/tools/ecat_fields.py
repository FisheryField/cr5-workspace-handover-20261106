
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

RX = [("0x6040 Controlword",0,2),("0x6060 Mode",2,1),("0x607A Target position",3,4),
      ("0x60FF Target velocity",7,4),("0x60B2 Torque offset",11,2),("0x6071 Target torque",13,2),
      ("0x6080 Max motor speed",15,4),("0x6085 Quick stop dec",19,4)]
TX = [("0x6041 Statusword",0,2),("0x6061 Mode display",2,1),("0x6064 Position actual",3,4),
      ("0x606C Velocity actual",7,4),("0x6077 Torque actual",11,2),("0x6075 Motor rated current",13,4),
      ("0x6076 Motor rated torque",17,4),("0x603F Error code",21,2),("0x6079 DC link voltage",23,4),
      ("0x6078 Current actual",27,2),("0x5000:02",29,2),("0x5000:03",31,2),("0x5002:03",39,4),
      ("0x5002:04",43,4),("0x606B Velocity demand",49,4),("0x6062 Position demand",53,4)]

def show(label, path, t):
    fr = frame_at(path,t)
    print("=== %s ===" % label)
    print("  -- RxPDO J1 块 (帧偏移 94 起, 45B) --")
    for nm,off,ln in RX:
        v = int.from_bytes(fr[94+off:94+off+ln],'little',signed=(ln==4))
        print("     %-26s @%3d  = %d" % (nm, 94+off, v))
    print("  -- TxPDO J1 块 (帧偏移 600 起, 57B) --")
    for nm,off,ln in TX:
        v = int.from_bytes(fr[600+off:600+off+ln],'little',signed=(ln==4))
        print("     %-26s @%3d  = %d" % (nm, 600+off, v))
    print()

Z="D:\\mydata\\workspace\\data\\codex_b\\ethercat_pcap\\zero32_calibration.pcap"
C="D:\\mydata\\workspace\\data\\codex_b\\ethercat_pcap\\capture315_ethercat.pcap1"
show("3.2.d.8  标定前 (J1 在零点)", Z, 1790063112.3)
show("3.1.5.0  标定后 2s", C, 1790065876.0)
show("3.1.5.0  上使能后/标定前", C, 1790065870.0)
