
import struct, collections
def readpcap(path):
    d=open(path,'rb').read(); off=24; out=[]
    while off+16<=len(d):
        ts,tus,incl,orig=struct.unpack_from("<IIII",d,off); off+=16
        out.append((ts+tus/1e6,d[off:off+incl])); off+=incl
    return out
def dgs(frame):
    if len(frame)<16 or frame[12:14]!=b'\x88\xa4': return []
    flen=struct.unpack_from('<H',frame,14)[0]&0x7ff
    off=16; end=min(16+flen,len(frame)); out=[]
    while off+12<=end:
        cmd,idx=frame[off],frame[off+1]
        adr=frame[off+2:off+6]
        lw=struct.unpack_from('<H',frame,off+6)[0]; dl=lw&0x7ff; more=(lw>>15)&1
        out.append((cmd, idx, adr, dl, frame[off+10:off+10+dl]))
        off+=12+dl
        if not more: break
    return out
fr=readpcap(r"D:\mydata\workspace\data\codex_b\ethercat_pcap\zero32_calibration.pcap")
tpl={}
for ts,pkt in fr:
    for cmd,idx,adr,dl,data in dgs(pkt):
        st=struct.unpack_from('<H',adr,0)[0]; off=struct.unpack_from('<H',adr,2)[0]
        if cmd==5 and off==0x1800 and dl>=32:
            key=(st,off)
            if key not in tpl: tpl[key]=data[:32]
print("=== 控制器写邮箱(FPWR 0x1800) 的原始前 24 字节，按站 ===")
for (st,off),v in sorted(tpl.items()):
    print("  st=0x%04x(%d) off=0x%04x : %s" % (st,st,off,v[:24].hex(' ')))
print()
# 响应
tpl2={}
for ts,pkt in fr:
    for cmd,idx,adr,dl,data in dgs(pkt):
        st=struct.unpack_from('<H',adr,0)[0]; off=struct.unpack_from('<H',adr,2)[0]
        if cmd==4 and off==0x1a30 and dl>=32:
            key=(st,off)
            if key not in tpl2 and data[6:7]==b'\x30': tpl2[key]=data[:24]
print("=== 控制器读邮箱(FPRD 0x1a30) 收到的响应前 24 字节（service=0x30）===")
for (st,off),v in sorted(tpl2.items()):
    print("  st=0x%04x(%d) off=0x%04x : %s" % (st,st,off,v.hex(' ')))
