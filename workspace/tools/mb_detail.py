
import struct, datetime, collections
def readpcap(path):
    d=open(path,'rb').read(); off=24; out=[]
    while off+16<=len(d):
        ts,tus,incl,orig=struct.unpack_from("<IIII",d,off); off+=16
        out.append((ts+tus/1e6,d[off:off+incl])); off+=incl
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
        out.append((cmd,idx,adr,dl,more,frame[off+10:off+10+dl]))
        off+=12+dl
        if not more: break
    return out
CMD={0:'NOP',1:'APRD',2:'APWR',3:'APRW',4:'FPRD',5:'FPWR',6:'FPRW',7:'BRD',8:'BWR',9:'BRW',10:'LRD',11:'LWR',12:'LRW',13:'ARMW',14:'FRMW'}
fr=readpcap(r"D:\mydata\workspace\data\codex_b\ethercat_pcap\zero32_calibration.pcap")
print("=== 每站所有 FPWR(0x1800) 事务的 mb[5] 与 mb[8] ===")
per=collections.defaultdict(list)
for ts,pkt in fr:
    for cmd,idx,adr,dl,more,data in dgs(pkt):
        st=struct.unpack_from('<H',adr,0)[0]; off=struct.unpack_from('<H',adr,2)[0]
        if cmd==5 and off==0x1800 and dl>=16:
            per[st].append((tstr(ts), data[5], data[7], data[8], data[9]|(data[10]<<8), data[11]))
for st in sorted(per):
    print("  st=0x%04x:" % st)
    for t,ch,typ,sdoc,ix,sub in per[st]:
        print("     %s  mb[5]=0x%02x mb[7]=0x%02x sdo=0x%02x idx=0x%04x sub=%d" % (t,ch,typ,sdoc,ix,sub))
print()
print("=== 每站所有 FPRD(0x1a30) 读到的应答 ===")
per2=collections.defaultdict(list)
for ts,pkt in fr:
    for cmd,idx,adr,dl,more,data in dgs(pkt):
        st=struct.unpack_from('<H',adr,0)[0]; off=struct.unpack_from('<H',adr,2)[0]
        if cmd==4 and off==0x1a30 and dl>=16:
            per2[st].append((tstr(ts), data[:16].hex(' ')))
for st in sorted(per2):
    print("  st=0x%04x:" % st)
    seen=set()
    for t,h in per2[st]:
        if h in seen: continue
        seen.add(h); print("     %s  %s" % (t,h))
print()
print("=== 含 FPWR(0x1800) 的帧里，所有数据报 ===")
shown=0
for ts,pkt in fr:
    ds=dgs(pkt)
    if any(c==5 and struct.unpack_from('<H',a,2)[0]==0x1800 for c,_,a,_,_,_ in ds):
        if shown>=3: break
        shown+=1
        print("  帧 %s len=%d  数据报数=%d" % (tstr(ts),len(pkt),len(ds)))
        for cmd,idx,adr,dl,more,data in ds:
            st=struct.unpack_from('<H',adr,0)[0]; off=struct.unpack_from('<H',adr,2)[0]
            print("     cmd=%-5s st=0x%04x off=0x%04x dl=%-4d more=%d data=%s" % (
                CMD.get(cmd&0xf,cmd), st, off, dl, more, data[:16].hex(' ')))
