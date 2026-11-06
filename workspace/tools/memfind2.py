
import tarfile, struct, sys
tf = tarfile.open(sys.argv[1], 'r:gz')
joints = [7.1219401359558109, -5.053975582122803, -5.103166103363037,
          -4.0680251121521, 0.00802020262926817, 89.00447082519531]
scale = 360.0/(20000*101)
signs = [-1,-1,1,-1,-1,-1]
counts = [int(round(j/scale*s)) for j,s in zip(joints,signs)]
print("joints =", joints)
print("scale  =", scale)
print("counts =", counts)
dpats = [(j, struct.pack('<d', j)) for j in joints]
ipats = []
for c in counts:
    for d in (-1,0,1):
        ipats.append((c+d, struct.pack('<i', c+d)))
manifest=''
members={}
for m in tf.getmembers():
    if m.name.endswith('manifest.txt'):
        manifest = tf.extractfile(m).read().decode('latin-1')
    if m.name.endswith('.bin'):
        members[m.name] = m
regions={}
for line in manifest.strip().split('\n'):
    p=line.split()
    if len(p)>=4: regions['memdump2/r%s.bin'%p[0]]=(p[1], int(p[3]))
print()
print("%-9s %-28s %10s  %s" % ("region","addr","size","hits"))
for name,(addr,sz) in regions.items():
    if name not in members: continue
    data = tf.extractfile(members[name]).read()
    dh=[]; ih=[]
    for j,pat in dpats:
        st=0
        while True:
            k=data.find(pat,st)
            if k<0: break
            dh.append((j,k)); st=k+1
    for c,pat in ipats:
        st=0
        while True:
            k=data.find(pat,st)
            if k<0: break
            ih.append((c,k)); st=k+1
    if dh or ih:
        print("%-9s %-28s %10d  D:%s  I:%s" % (name.split('/')[-1], addr, len(data),
              ' '.join('%g@%d'%(j,k) for j,k in dh[:8]),
              ' '.join('%d@%d'%(c,k) for c,k in ih[:8])))
