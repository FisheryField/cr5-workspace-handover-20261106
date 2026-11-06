
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
        out.append((cmd,ado,adp,dl,off+10))
        off+=12+dl
        if not more: break
    return out

path=sys.argv[1]; target=float(sys.argv[2]); label=sys.argv[3]
pkts=[p for p in read_pcap(path) if len(p[1])==1111]
best=min(pkts, key=lambda p: abs(p[0]-target))
ts,frame=best
print("%s  frame @ %.3f (dt=%+.3f) len=%d" % (label, ts, ts-target, len(frame)))
for cmd,ado,adp,dl,doff in dgs(frame):
    print("   dg cmd=%-2d ado=0x%04x len=%-4d data_off=%d" % (cmd,ado,dl,doff))
tx=None
for cmd,ado,adp,dl,doff in dgs(frame):
    if cmd==10 and dl>100: tx=(doff,dl)
print("TxPDO at frame offset %d len %d" % tx)
doff,dl=tx
data=frame[doff:doff+dl]
vals=[int.from_bytes(data[i:i+4],'little',signed=True) for i in range(0,dl-3,4)]
print("int32 count=%d   (marker * = codex 找到的那 6 个偏移)" % len(vals))
line=""
for i,v in enumerate(vals):
    off=doff+i*4
    mark='*' if off in (603,660,717,810,879,950) else ' '
    line += "%s%3d@%4d=%-9d " % (mark,i,off,v)
    if (i+1)%5==0: print("  "+line); line=""
if line: print("  "+line)
