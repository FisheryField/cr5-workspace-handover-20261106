
import struct
d=open(r"D:\mydata\workspace\data\codex_b\ethercat_pcap\zero32_calibration.pcap",'rb').read()
off=24; frames=[]
while off+16<=len(d):
    ts,tus,incl,orig=struct.unpack_from("<IIII",d,off); off+=16
    frames.append((ts+tus/1e6, d[off:off+incl])); off+=incl
# 找那个 589 字节、含 FPRD 0x1a30 的帧
for ts,pkt in frames:
    if len(pkt)!=589: continue
    if pkt[12:14]!=b'\x88\xa4': continue
    if pkt[18:22] != b'\xeb\x03\x30\x1a': continue
    print("找到帧 len=%d" % len(pkt))
    print("前 48 字节:", pkt[:48].hex(' '))
    ec = pkt[14] | ((pkt[15]&0x07)<<8)
    print("ECat header: len=%d type=%d  (帧总长应为 14+2+%d=%d)" % (ec, (pkt[15]>>4)&1, ec, 16+ec))
    # 手动逐数据报解析
    o=16; n=0
    while o+12 <= 16+ec:
        cmd,idx = pkt[o], pkt[o+1]
        st = pkt[o+2]|(pkt[o+3]<<8); of = pkt[o+4]|(pkt[o+5]<<8)
        lw = pkt[o+6]|(pkt[o+7]<<8); dl = lw & 0x7ff; more=(lw>>15)&1
        wkc = pkt[o+10+dl]|(pkt[o+11+dl]<<8)
        print("  dg%d: cmd=0x%02x idx=0x%02x st=0x%04x off=0x%04x dl=%-4d more=%d wkc=%d" % (n,cmd,idx,st,of,dl,more,wkc))
        if n==0:
            print("       data前16: %s" % pkt[o+10:o+26].hex(' '))
            print("       数据报总长 = 10+%d+2 = %d ; 下一个数据报应从 %d 开始" % (dl, 12+dl, o+12+dl))
        o += 12+dl; n+=1
        if not more: break
    print("  解析完 %d 个数据报, 结束于 offset %d (应为 %d)" % (n, o, 16+ec))
    print("  剩余字节: %d" % (len(pkt)-o))
    if len(pkt)-o > 0:
        print("  尾部: %s" % pkt[o:o+40].hex(' '))
    break
