
import struct, sys, datetime, collections
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
name={0x32D8:'3.2.D.8',0x3150:'3.1.5.0'}
def scan(path):
    net,pk=load(path)
    pk=[p for p in pk if len(p[1])==1111]
    print("=== %s  network=%d  frames=%d  t0=%s ===" % (path.split('\\')[-1], net, len(pk),
          datetime.datetime.fromtimestamp(pk[0][0]+8*3600, datetime.UTC).strftime('%m-%d %H:%M:%S')))
    if not pk: return
    seen=collections.defaultdict(collections.Counter)
    tfirst={}; tlast={}
    for ts,d in pk:
        for off in range(0, len(d)-1):
            v=struct.unpack_from('<H',d,off)[0]
            if v in name:
                seen[off][v]+=1
                if off not in tfirst: tfirst[off]=ts
                tlast[off]=ts
    print("   version-word offsets (whole frame):")
    for off in sorted(seen):
        print("     off=%4d  %-24s  from %+7.1fs to %+7.1fs" % (
            off, ', '.join('%s x%d'%(name[v],n) for v,n in seen[off].most_common()),
            tfirst[off]-pk[0][0], tlast[off]-pk[0][0]))
    print()
scan(sys.argv[1]); scan(sys.argv[2]); scan(sys.argv[3])
