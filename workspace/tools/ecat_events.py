
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
RX=[97,142,187,232,287,334]
TX=[603,660,717,810,879,950]

def events(path, post, json_t, label):
    pk=sorted([p for p in read_pcap(path) if len(p[1])==1111])
    print("=== %s  (POST at t=%+.3f, JSON write at t=%+.3f) ===" % (label, 0.0, json_t-post))
    print("  轴 | 0x607A(Rx) 变 0 的时刻 | 0x6064(Tx) 变 0 的时刻")
    for i in range(6):
        rx0=tx0=None
        for ts,d in pk:
            if ts<post-1.0: continue
            if ts>post+8.0: break
            r=struct.unpack_from('<i',d,RX[i])[0]
            x=struct.unpack_from('<i',d,TX[i])[0]
            if rx0 is None and r==0 and ts>post-0.5: rx0=ts-post
            if tx0 is None and x==0 and ts>post-0.5: tx0=ts-post
        print("  J%d | %-22s | %-22s" % (i+1,
              ("%+.3f s" % rx0) if rx0 is not None else "不变 0",
              ("%+.3f s" % tx0) if tx0 is not None else "不变 0"))
    # 逐帧采样头 3.5 秒
    print("  --- 逐帧 (每 0.1s 取样, J1/J2) ---")
    t=post-0.5
    while t<=post+3.2:
        ts,d=min(pk,key=lambda p:abs(p[0]-t))
        print("     t=%+6.3f  J1 Rx=%-9d Tx=%-9d | J2 Rx=%-9d Tx=%-9d" % (
            ts-post,
            struct.unpack_from('<i',d,RX[0])[0], struct.unpack_from('<i',d,TX[0])[0],
            struct.unpack_from('<i',d,RX[1])[0], struct.unpack_from('<i',d,TX[1])[0]))
        t+=0.1
    print()
Z="D:\\mydata\\workspace\\data\\codex_b\\ethercat_pcap\\zero32_calibration.pcap"
C="D:\\mydata\\workspace\\data\\codex_b\\ethercat_pcap\\capture315_ethercat.pcap1"
# POST: 3.2.d.8 = 1790063115.448, JSON = 1790063116.366 ; 3.1.5 = POST 1790065873.998
events(Z, 1790063115.448, 1790063116.366, "3.2.D.8")
events(C, 1790065873.998, 1790065874.9, "3.1.5.0 (JSON 写入时刻为估计)")
