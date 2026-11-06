
import struct, sys
data=open(sys.argv[1],'rb').read()
n=len(data)
print("file=%s size=%d" % (sys.argv[1], n))
def words(off, cnt): return [struct.unpack_from('<H', data, off+2*i)[0] for i in range(cnt)]
w=words(0, 64)
print("  PDI Control=0x%04x  PDI Config=0x%04x" % (w[0], w[1]))
print("  VendorID=0x%08x  ProductCode=0x%08x  Revision=0x%08x  Serial=0x%08x" %
      (struct.unpack_from('<I',data,16)[0], struct.unpack_from('<I',data,20)[0],
       struct.unpack_from('<I',data,24)[0], struct.unpack_from('<I',data,28)[0]))
print("  EEPROM size/version words 62..63: 0x%04x 0x%04x" % (w[62], w[63]))

off=128
cats={}
strings={}
while off+4 <= n:
    ctype, clen = struct.unpack_from('<HH', data, off)
    if ctype == 0xFFFF: break
    body = data[off+4: off+4+clen*2]
    cats.setdefault(ctype, []).append(body)
    off += 4 + clen*2

# strings (0x0A): after 1 word count, then null-terminated strings
for b in cats.get(0x0A, []):
    cnt=struct.unpack_from('<H', b, 0)[0]
    p=2; idx=0
    while p < len(b):
        e=b.find(b'\x00', p)
        if e<0: e=len(b)
        strings[idx]=b[p:e].decode('latin-1'); idx+=1
        p=e+1
print("  categories:", sorted('0x%04x(%d bytes)'%(k,len(v[0])) for k,v in cats.items()))
print("  strings: %d" % len(strings))

def dump_pdo(cat, label):
    for b in cats.get(cat, []):
        print("  --- %s category ---" % label)
        i=0
        while i+8 <= len(b):
            idx, sub, bitlen, name, flags = struct.unpack_from('<HBBHH', b, i)
            if idx==0 and sub==0 and bitlen==0: break
            print("    0x%04x:%02d  %3d bits (%5.1f B)  name=%-24s flags=0x%04x"
                  % (idx, sub, bitlen, bitlen/8.0, strings.get(name,'?'), flags))
            i+=8
for c,l in ((0x002A,'TxPDO (从站→主站)'), (0x002B,'RxPDO (主站→从站)')):
    dump_pdo(c,l)
for c,l in ((0x0028,'FMMU'),(0x0029,'SyncM'),(0x001E,'General')):
    for b in cats.get(c,[]):
        print("  --- %s (%d bytes) ---" % (l,len(b)))
        print("    "+' '.join('%02x'%x for x in b[:64]))
