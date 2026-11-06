
import struct, sys, datetime
def load(path, limit=400000):
    out=[]
    with open(path,'rb') as f:
        gh=f.read(24)
        if len(gh)<24: return -1,out
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
            if net==276: d=b'\x00'*12+b'\x88\xa4'+d[20:]
            out.append((ts+tu/1e6,d))
    return net,out
# TxPDO 数据起点（含以太网头时）= 498；6 个块按 3.1.5.0/3.2.D.8 两版共有的块尺寸
BLK=[(600,57),(657,57),(714,57),(807,93),(876,69),(947,71)]
name={0x32D8:'3.2.D.8',0x3150:'3.1.5.0'}
for path,label in [(sys.argv[1],'A'),(sys.argv[2],'B')]:
    net,pk=load(path)
    pk=[p for p in pk if len(p[1])==1111]
    ts0=pk[0][0]
    print("=== %s  network=%d 帧=%d  t0=%s ===" % (path.split('\\')[-1], net, len(pk),
          datetime.datetime.fromtimestamp(ts0+8*3600, datetime.UTC).strftime('%m-%d %H:%M:%S')))
    for i,(b,sz) in enumerate(BLK):
        hits={}
        for ts,d in pk:
            for off in range(b, b+sz-1):
                v=struct.unpack_from('<H', d, off)[0]
                if v in (0x32D8,0x3150):
                    hits.setdefault((off-b, v), 0)
                    hits[(off-b, v)] += 1
        s='  '.join('块内+%d=%s x%d' % (o, name[v], n) for (o,v),n in sorted(hits.items()))
        print("   J%d 块起点 %d : %s" % (i+1, b, s or '(未找到)'))
    print()
