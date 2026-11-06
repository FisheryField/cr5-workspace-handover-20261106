
import tarfile, struct, sys, hashlib
tf = tarfile.open(sys.argv[1],'r:gz')
joints=[7.1219401359558105,-5.053975582122803,-5.103166103363037,-4.0680251121521,0.00802020262926817,89.00447082519531]
pats=[(j,struct.pack('<d',j)) for j in joints]
for name in ('r15_a.bin','r15_b.bin'):
    for m in tf.getmembers():
        if m.name.endswith(name):
            d=tf.extractfile(m).read()
            print("=== %s size=%d sha=%s ===" % (name,len(d),hashlib.sha256(d).hexdigest()[:12]))
            for j,pat in pats:
                hits=[];st=0
                while True:
                    k=d.find(pat,st)
                    if k<0: break
                    hits.append(k); st=k+1
                if hits: print("   %-22g at %s" % (j,hits[:10]))
            # 相邻差异计数
            diff=sum(1 for i in range(0,min(len(d),260000),4096) if d[i:i+16]!=b'\x00'*16)
            print("   非零 16 字节块(每 4096 抽样) = %d" % diff)
