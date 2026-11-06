
import struct, sys, datetime, collections
def readpcap(path):
    d=open(path,'rb').read()
    magic,=struct.unpack_from("<I",d,0)
    if magic==0xa1b2c3d4: endian="<"
    elif magic==0xd4c3b2a1: endian=">"
    else: endian="<"
    vmaj,vmin,tz,sig,snap,link=struct.unpack_from(endian+"HHiIII",d,4)
    off=24; out=[]
    while off+16<=len(d):
        ts,tus,incl,orig=struct.unpack_from(endian+"IIII",d,off); off+=16
        pkt=d[off:off+incl]; off+=incl
        out.append((ts+tus/1e6,pkt,link,orig))
    return link,out
def tstr(t): return datetime.datetime.fromtimestamp(t).strftime("%H:%M:%S.%f")[:-3]
for path,label in ((r"D:\mydata\workspace\data\codex_b\ethercat_pcap\zero32_calibration.pcap","3.2.D.8 标定"),
                   (r"D:\mydata\workspace\data\codex_b\ethercat_pcap\capture315_ethercat.pcap0","3.1.5.0 a"),
                   (r"D:\mydata\workspace\data\codex_b\ethercat_pcap\capture315_ethercat.pcap1","3.1.5.0 b")):
    try: link,fr=readpcap(path)
    except Exception as e:
        print("%s: 打不开 %s"%(label,e)); continue
    lens=collections.Counter(len(p[1]) for p in fr)
    print("=== %s  linktype=%d  帧数=%d" % (label,link,len(fr)))
    print("    帧长分布(top8): %s" % lens.most_common(8))
    odd=[p for p in fr if len(p[1])!=1111]
    print("    非1111帧 = %d" % len(odd))
    if odd:
        # 按 ADO 分类
        cnt=collections.Counter()
        for t,pkt,_,orig in odd[:4000]:
            if len(pkt)<14+2: continue
            if struct.unpack_from(">H",pkt,12)[0]!=0x88a4: 
                cnt[("非EtherCAT",len(pkt))]+=1; continue
            # EtherCAT datagram
            try:
                dg=pkt[14:]
                cmd=dg[0]; idx=dg[1]
                adp,ado=struct.unpack_from("<HH",dg,2)
                ln=struct.unpack_from("<H",dg,6)[0]&0x7ff
                cnt[("cmd%d"%cmd, "ADP0x%x"%adp, "ADO0x%x"%ado, "len%d"%ln, "frm%d"%len(pkt))]+=1
            except: cnt[("解析失败",len(pkt))]+=1
        print("    非1111帧分类:")
        for k,v in cnt.most_common(20): print("      %-60s x%d" % (str(k), v))
        print("    最早的 12 个非1111帧:")
        for t,pkt,_,orig in odd[:12]:
            print("      %s len=%-5d %s" % (tstr(t), len(pkt), pkt[:72].hex()))
    print()
