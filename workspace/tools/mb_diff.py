
import struct, datetime, collections
def readpcap(path):
    d=open(path,'rb').read()
    off=24; out=[]
    while off+16<=len(d):
        ts,tus,incl,orig=struct.unpack_from("<IIII",d,off); off+=16
        out.append((ts+tus/1e6, d[off:off+incl])); off+=incl
    return out
def tstr(t): return datetime.datetime.fromtimestamp(t).strftime("%H:%M:%S.%f")[:-3]
def dgs(frame):
    if len(frame)<16 or frame[12:14]!=b'\x88\xa4': return []
    flen=struct.unpack_from('<H',frame,14)[0]&0x7ff
    off=16; end=min(16+flen,len(frame)); out=[]
    while off+12<=end:
        cmd,idx=frame[off],frame[off+1]
        adr=frame[off+2:off+6]
        lw=struct.unpack_from('<H',frame,off+6)[0]; dl=lw&0x7ff; more=(lw>>15)&1
        out.append((cmd, adr, dl, frame[off+10:off+10+dl]))
        off+=12+dl
        if not more: break
    return out
CMD={0:'NOP',1:'APRD',2:'APWR',3:'APRW',4:'FPRD',5:'FPWR',6:'FPRW',7:'BRD',8:'BWR',9:'BRW',10:'LRD',11:'LWR',12:'LRW',13:'ARMW',14:'FRMW'}
res={}
for path,label in ((r"D:\mydata\workspace\data\codex_b\ethercat_pcap\zero32_calibration.pcap","3.2.D.8"),
                   (r"D:\mydata\workspace\data\codex_b\ethercat_pcap\capture315_ethercat.pcap1","3.1.5.0")):
    fr=readpcap(path)
    items=[]
    for ts,pkt in fr:
        if len(pkt)==1111: continue
        for cmd,adr,dl,data in dgs(pkt):
            lo=struct.unpack_from('<H',adr,0)[0]; hi=struct.unpack_from('<H',adr,2)[0]
            items.append((tstr(ts), CMD.get(cmd&0xf,cmd), lo, hi, dl, data[:20].hex()))
    res[label]=items
    print("=== %s : 邮箱/非周期数据报 %d 个 ===" % (label, len(items)))
    for it in items:
        print("   %s %-5s st=0x%04x ado=0x%04x dl=%-4d %s" % it)
    print()
a=[x[1:] for x in res["3.2.D.8"]]
b=[x[1:] for x in res["3.1.5.0"]]
print("=== 逐项比对（忽略时间戳）===")
print("  3.2.D.8 项数=%d   3.1.5.0 项数=%d" % (len(a),len(b)))
if a==b: print("  ★ 完全相同（逐字节）")
else:
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y: print("  差异 @%d:\n    3.2.D.8: %s\n    3.1.5.0: %s" % (i,x,y))
