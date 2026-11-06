
p = r'D:\mydata\workspace\libdataSvr.so.bin'
d=open(p,'rb').read()
start=0x20b7e0; end=0x20b8b0
blob=d[start:end]
print("原始字节 + 逐串标注 (0x%x .. 0x%x):" % (start,end))
print(" ".join("%02x"%b for b in blob))
print()
cur=b''; base=start; i=0
while i < len(blob):
    c=blob[i]
    if 32<=c<127:
        if not cur: base=start+i
        cur+=bytes([c])
    else:
        if len(cur)>=1:
            print("  0x%06x (+%d) : %r" % (base, base-start, cur.decode('latin-1')))
        cur=b''
    i+=1
if cur: print("  0x%06x (+%d) : %r" % (base, base-start, cur.decode('latin-1')))
