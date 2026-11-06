
import struct, sys, collections

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

def decode_ecat(frame):
    """return list of dicts for each datagram, or None if not EtherCAT"""
    if len(frame) < 16: return None
    if frame[12:14] != b'\x88\xa4': return None
    hdr = struct.unpack_from('<H', frame, 14)[0]
    flen = hdr & 0x7FF
    ftype = (hdr >> 12) & 0xF
    off = 16
    end = min(16 + flen, len(frame))
    out=[]
    while off + 12 <= end:
        cmd, idx = frame[off], frame[off+1]
        addr = struct.unpack_from('<I', frame, off+2)[0]
        lw   = struct.unpack_from('<H', frame, off+6)[0]
        dlen = lw & 0x7FF
        more = (lw >> 15) & 1
        data = frame[off+10: off+10+dlen]
        wkc  = struct.unpack_from('<H', frame, off+10+dlen)[0] if off+12+dlen <= len(frame) else None
        out.append(dict(cmd=cmd, idx=idx, addr=addr, len=dlen, more=more, data=data, wkc=wkc, off=off))
        off += 12 + dlen
        if not more: break
    return ftype, out

path = sys.argv[1]
pkts = read_pcap(path)
print("frames=%d" % len(pkts))

cmdcount = collections.Counter()
addrhist = collections.Counter()
odd = []
fail = 0
for ts,d in pkts:
    r = decode_ecat(d)
    if r is None: fail += 1; continue
    ftype, dgs = r
    for g in dgs:
        cmdcount[CMD.get(g['cmd'], g['cmd'])] += 1
        addrhist[(CMD.get(g['cmd'],g['cmd']), g['addr'] & 0xFFFF0000, g['len'])] += 1
    if len(d) != 1111:
        odd.append((ts, len(d), dgs, d))

print("non-ethercat frames: %d" % fail)
print("datagram commands:", cmdcount.most_common())
print("--- address groups (cmd, addr>>16, len) top 15 ---")
for k,v in addrhist.most_common(15):
    print("   %-6s addr_hi=0x%08x len=%-5d x%d" % (k[0], k[1], k[2], v))
print("--- odd (non-1111) frames: %d ---" % len(odd))
seen=collections.Counter()
for ts,l,dgs,d in odd:
    key=(l, tuple((CMD.get(g['cmd'],g['cmd']), g['addr'], g['len']) for g in dgs))
    seen[key]+=1
for k,v in seen.most_common():
    print("  len=%d x%d dgs=%s" % (k[0], v, k[1]))
