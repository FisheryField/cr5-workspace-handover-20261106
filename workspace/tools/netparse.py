
import struct, re, sys, collections
p = sys.argv[1]
d=open(p,'rb').read()
gh=d[:24]; endian='<' if gh[:4]==b'\xd4\xc3\xb2\xa1' else '>'
net=struct.unpack(endian+'I',gh[20:24])[0]
pos=24; pkts=[]; flows=collections.defaultdict(bytes)
while pos+16<=len(d):
    ts,tu,cap,orig=struct.unpack_from(endian+'IIII',d,pos); pos+=16
    fr=d[pos:pos+cap]; pos+=cap
    if len(fr)<34: continue
    if fr[12:14]!=b'\x08\x00': continue
    ihl=(fr[14]&0xf)*4
    proto=fr[23]
    if proto!=6: continue
    src='.'.join(str(b) for b in fr[26:30]); dst='.'.join(str(b) for b in fr[30:34])
    tcp=14+ihl
    sp,dp=struct.unpack_from('>HH',fr,tcp)
    doff=((fr[tcp+12]>>4)&0xf)*4
    payload=fr[tcp+doff:]
    if not payload: continue
    k=(src,sp,dst,dp)
    flows[k]+=payload
print("TCP 流 %d 条:" % len(flows))
for k,v in sorted(flows.items(), key=lambda x:-len(x[1])):
    print("  %s:%d -> %s:%d   %d bytes" % (k[0],k[1],k[2],k[3],len(v)))
print()
for k,v in flows.items():
    if b'HTTP' in v[:200] or b'POST' in v[:200] or b'GET ' in v[:200]:
        txt=v.decode('latin-1')
        for m in re.finditer(r'(GET|POST|PUT|DELETE)\s+(\S+)\s+HTTP/[\d.]+', txt):
            print("  REQ  %s %s" % (m.group(1), m.group(2)))
        for m in re.finditer(r'HTTP/[\d.]+ (\d{3})', txt):
            print("  RESP %s" % m.group(1))
