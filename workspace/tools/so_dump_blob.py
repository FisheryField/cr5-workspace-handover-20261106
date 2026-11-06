
p = r'D:\mydata\workspace\libdataSvr.so.bin'
d=open(p,'rb').read()
start=0x20b780; end=0x20ba20
blob=d[start:end]
cur=b''; base=start
i=0
print("libdataSvr.so  @0x%x .. 0x%x 的可打印串：" % (start,end))
while i < len(blob):
    c=blob[i]
    if 32<=c<127:
        if not cur: base=start+i
        cur+=bytes([c])
    else:
        if len(cur)>=3:
            print("  0x%06x : %s" % (base, cur.decode('latin-1')))
        cur=b''
    i+=1
if len(cur)>=3: print("  0x%06x : %s" % (base, cur.decode('latin-1')))
