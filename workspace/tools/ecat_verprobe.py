
import struct, sys, collections, datetime
def load(path, limit=400000):
    out=[]
    with open(path,'rb') as f:
        gh=f.read(24)
        if len(gh)<24: return 0,out
        if gh[:4]==b'\xd4\xc3\xb2\xa1': endian='<'
        elif gh[:4]==b'\xa1\xb2\xc3\xd4': endian='>'
        else: return -1,out
        net=struct.unpack(endian+'I',gh[20:24])[0]
        while len(out)<limit:
            h=f.read(16)
            if len(h)<16: break
            ts,tu,cap,orig=struct.unpack(endian+'IIII',h)
            d=f.read(cap)
            if len(d)<cap: break
            if net==276:      # DLT_LINUX_SLL2: 20 字节 cooked 头，其后是 EtherCAT 帧
                d=b'\x00'*12+b'\x88\xa4'+d[20:]
            out.append((ts+tu/1e6,d))
    return net,out

BLK=[600,657,714,807,876,947]   # 含以太网头时的块起点
def probe(path):
    net,pk=load(path)
    print("=== %s  (network=%d) ===" % (path.split('\\')[-1], net))
    pk=[p for p in pk if len(p[1])==1111]
    if not pk:
        print("   无 1111 字节帧"); return
    print("   帧数=%d  跨度=%.1fs  t0=%s" % (len(pk), pk[-1][0]-pk[0][0],
          datetime.datetime.fromtimestamp(pk[0][0]+8*3600, datetime.UTC).strftime('%m-%d %H:%M:%S')))
    for i,b in enumerate(BLK):
        c=collections.Counter()
        for ts,d in pk:
            c[struct.unpack_from('<H', d, b+42)[0]] += 1
        top=c.most_common(3)
        name={0x32D8:'3.2.D.8',0x3150:'3.1.5.0'}
        print("   J%d : %s" % (i+1, ', '.join('%s(0x%04X) x%d' % (name.get(v,'?'), v, n) for v,n in top)))
for p in sys.argv[1:]: probe(p)
