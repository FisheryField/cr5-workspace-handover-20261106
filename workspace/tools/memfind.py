
import tarfile, struct, io, sys
tf = tarfile.open(sys.argv[1], 'r:gz')
doubles = [7.1219401359558109, -5.053975582122803, -5.103166103363037,
           -4.0680251121521, 0.00802020262926817, 89.00447082519531]
pats = [(d, struct.pack('<d', d)) for d in doubles]
manifest = ''
for m in tf.getmembers():
    if m.name.endswith('manifest.txt'):
        manifest = tf.extractfile(m).read().decode('latin-1')
    if m.name.endswith('maps.txt'):
        maps = tf.extractfile(m).read().decode('latin-1')
print("--- manifest ---"); print(manifest.strip())
regions = {}
base = None
for line in manifest.strip().split('\n'):
    p = line.split()
    if len(p) >= 3: regions['memdump/r%s.bin' % p[0]] = (p[1], int(p[3]) if len(p)>3 else 0)
print()
for m in tf.getmembers():
    if not m.name.endswith('.bin'): continue
    data = tf.extractfile(m).read()
    hits = []
    for d, pat in pats:
        st = 0
        while True:
            j = data.find(pat, st)
            if j < 0: break
            hits.append((d, j)); st = j+1
    print("%s  size=%-8d  double hits=%d  %s" % (m.name.split('/')[-1], len(data), len(hits),
          ' '.join('%g@%d' % (d,j) for d,j in hits[:6])))
