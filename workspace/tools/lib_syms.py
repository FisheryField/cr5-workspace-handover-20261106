
import struct, sys, os
p = r'D:\mydata\workspace\libdataSvr.so.bin'
print("exists:", os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else 0)
d=open(p,'rb').read()
# ELF32
assert d[:4]==b'\x7fELF'
cls=d[4]; endian='<' if d[5]==1 else '>'
e_shoff=struct.unpack_from(endian+'I',d,0x20)[0]
e_shentsize=struct.unpack_from(endian+'H',d,0x2e)[0]
e_shnum=struct.unpack_from(endian+'H',d,0x30)[0]
e_shstrndx=struct.unpack_from(endian+'H',d,0x32)[0]
secs=[]
for i in range(e_shnum):
    o=e_shoff+i*e_shentsize
    name,typ,flags,addr,off,size,link,info,align,entsize=struct.unpack_from(endian+'IIIIIIIIII',d,o)
    secs.append(dict(name=name,type=typ,addr=addr,off=off,size=size,link=link,entsize=entsize))
shstr=secs[e_shstrndx]
def sname(n):
    o=shstr['off']+n
    e=d.index(b'\x00',o)
    return d[o:e].decode('latin-1')
for s in secs: s['sname']=sname(s['name'])
symtab=[s for s in secs if s['type']==2]
print("符号表节:", [(s['sname'], s['size'], s['entsize']) for s in symtab])
strtab=None
if symtab:
    st=symtab[0]
    strtab=secs[st['link']]
syms=[]
if symtab and strtab:
    st=symtab[0]
    n=st['size']//st['entsize']
    for i in range(n):
        o=st['off']+i*st['entsize']
        nm,val,size,info,other,shndx=struct.unpack_from(endian+'IIIBBH',d,o)
        e=d.index(b'\x00', strtab['off']+nm)
        s=d[strtab['off']+nm:e].decode('latin-1')
        syms.append((s,val,size,info&0xf,info>>4,shndx))
print("符号数:", len(syms))
KEEP=('readServoParams','parseAndReqGetServoParams','exitSDOWRThd','modifyServoParams','SDOWR','parseAndReqSetServoParams','caliHome','updateEncoderData')
for s,val,size,styp,bind,shndx in syms:
    if any(k in s for k in KEEP):
        print("  0x%08x size=%-6d type=%d  %s" % (val,size,styp,s))
