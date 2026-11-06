
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
def dgs(frame):
    flen=struct.unpack_from('<H',frame,14)[0]&0x7FF
    off=16; end=min(16+flen,len(frame)); out=[]
    while off+12<=end:
        cmd,idx=frame[off],frame[off+1]
        adp=struct.unpack_from('<H',frame,off+2)[0]
        ado=struct.unpack_from('<H',frame,off+4)[0]
        lw=struct.unpack_from('<H',frame,off+6)[0]; dl=lw&0x7FF; more=(lw>>15)&1
        out.append((cmd,ado,adp,dl,frame[off+10:off+10+dl]))
        off+=12+dl
        if not more: break
    return out
CMD={1:'APRD',2:'APWR',4:'FPRD',5:'FPWR'}
def sdo(b):
    if len(b)<8: return "(短)"
    mb_len,mb_addr=struct.unpack_from('<HH',b,0)
    ch,prio=b[4],b[5]
    coe=b[6:]
    if len(coe)<2: return "(空)"
    hdr=struct.unpack_from('<H',coe,0)[0]
    svc=hdr>>12
    cmd=coe[2] if len(coe)>2 else None
    idx=struct.unpack_from('<H',coe,3)[0] if len(coe)>5 else None
    sub=coe[5] if len(coe)>5 else None
    data=coe[6:] if len(coe)>6 else b''
    ccs=(cmd>>5)&7 if cmd is not None else None
    return "mblen=%-3d CoE=0x%04x(svc %d) cmd=0x%02x ccs=%s idx=0x%04x sub=%d data=%s" % (
        mb_len,hdr,3 if svc==3 else svc, cmd or 0, ccs, idx or 0, sub or 0, data[:16].hex())

for path,base,label in [(sys.argv[1],float(sys.argv[2]),'A'),(sys.argv[3],float(sys.argv[4]),'B')]:
    print("################ %s : %s ################" % (label, path.split('\\')[-1]))
    for ts,d in sorted(read_pcap(path), key=lambda p:p[0]):
        if len(d)==1111: continue
        for cmd,ado,adp,dl,data in dgs(d):
            if ado in (0x1800,0x1a30) and adp==1003:
                print("  t=%+.3fs %-5s ADO=0x%04x ADP=%d  %s" % (ts-base, CMD.get(cmd,cmd), ado, adp, sdo(data)))
                print("      raw[0:32]: %s" % data[:32].hex())
    print()
Z="D:\\mydata\\workspace\\data\\codex_b\\ethercat_pcap\\zero32_calibration.pcap"
C="D:\\mydata\\workspace\\data\\codex_b\\ethercat_pcap\\capture315_ethercat.pcap1"
print("(基准时刻 = 标定请求时刻)")
import subprocess
subprocess.run([sys.executable, __file__ if False else '-c','pass'])
