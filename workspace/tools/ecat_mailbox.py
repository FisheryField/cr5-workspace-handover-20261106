
import struct, sys, datetime
CMD = {0:'NOP',1:'APRD',2:'APWR',3:'APRW',4:'FPRD',5:'FPWR',6:'FPRW',7:'BRD',8:'BWR',9:'BRW',
       10:'LRD',11:'LWR',12:'LRW',13:'ARMW',14:'FRMW'}
def read_pcap(path):
    with open(path,'rb') as f:
        gh=f.read(24)
        endian = '<' if gh[:4] in (b'\xd4\xc3\xb2\xa1', b'\x4d\x3c\xb2\xa1') else '>'
        pkts=[]
        while True:
            h=f.read(16)
            if len(h)<16: break
            ts,tu,cap,orig=struct.unpack(endian+'IIII',h)
            d=f.read(cap)
            if len(d)<cap: break
            pkts.append((ts+tu/1e6,d))
        return pkts
def dgs(frame):
    if frame[12:14]!=b'\x88\xa4': return []
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

for path,base,label in [(sys.argv[1], float(sys.argv[2]), 'A'), (sys.argv[3], float(sys.argv[4]), 'B')]:
    pkts=read_pcap(path)
    print("=== %s : %s frames=%d span=%.1fs ===" % (label, path.split('\\')[-1], len(pkts), pkts[-1][0]-pkts[0][0]))
    t0=pkts[0][0]
    print("    t0(UTC+8) = %s" % datetime.datetime.fromtimestamp(t0+8*3600, datetime.UTC).strftime('%Y-%m-%d %H:%M:%S'))
    mail=[]
    for ts,d in pkts:
        for cmd,ado,adp,dl,data in dgs(d):
            if ado in (0x1800,0x1a30):
                mail.append((ts-t0, ts-base, CMD.get(cmd), ado, adp, data))
    print("    mailbox datagrams: %d" % len(mail))
    for rel,relcal,c,ado,adp,data in mail:
        mb_len,mb_addr=struct.unpack_from('<HH',data,0)
        body=data[6:6+max(0,mb_len-2)]
        print("      t=%+7.3fs  vs_calib=%+7.3fs  %-5s ADO=0x%04x ADP=%d mblen=%d | %s" % (rel, relcal, c, ado, adp, mb_len, body[:48].hex()))
    print()
