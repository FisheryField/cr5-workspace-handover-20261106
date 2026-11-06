
import struct, json
from capstone import *
P = r"D:\mydata\workspace\libdataSvr.so.bin"
d = open(P,'rb').read()
e_shoff, = struct.unpack_from("<I", d, 32)
e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", d, 46)
def sh(i):
    o=e_shoff+i*e_shentsize
    n,t,f,a,off,sz,lk,inf,al,ent = struct.unpack_from("<IIIIIIIIII", d, o)
    return dict(idx=i,name=n,typ=t,flags=f,addr=a,offset=off,size=sz,link=lk,info=inf,entsize=ent)
secs=[sh(i) for i in range(e_shnum)]
shstr=secs[e_shstrndx]
def sname(n):
    e=d.index(b"\x00", shstr["offset"]+n); return d[shstr["offset"]+n:e].decode("ascii","replace")
for s in secs: s["sname"]=sname(s["name"])
S={}
for s in secs: S.setdefault(s["sname"], s)
def a2o(addr):
    for s in secs:
        if s["typ"]!=8 and s["addr"]<=addr<s["addr"]+s["size"]:
            return s["offset"]+(addr-s["addr"])
    return None
plt={int(k,16):v for k,v in json.load(open(r'D:\mydata\workspace\tools\plt_map.json')).items()}
print("=== 本函数用到的被调函数全名 ===")
for stub in (0xba8fc,0xba750,0xb4560,0xbc108,0xb7d04,0xb8b78,0xb53c8,0xb47d4,0xb86ec,0xb4868,0xb4a54,0xb3d7c,0xb6090):
    print("  0x%06x  %s" % (stub, plt.get(stub,"?")))
# 读字面量
def lit(a):
    o=a2o(a)
    v,=struct.unpack_from("<I", d, o)
    return v
def cstr(a):
    o=a2o(a)
    if o is None: return None
    try: e=d.index(b"\x00", o)
    except: return None
    if e-o>200: return None
    b=d[o:e]
    try: t=b.decode('utf-8')
    except: return b.decode('latin-1')
    return t
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB)
code=d[a2o(0xec03c):a2o(0xec03c)+1080]
ins={i.address:i for i in md.disasm(code,0xec03c)}
def pcrel(a, which='r'):
    i=ins[a]
    disp=int(i.op_str.split('#')[-1].rstrip(']'),16)
    la=((a+4)&~3)+disp
    return lit(la)
def chain(a):
    "ldr + add pc -> final address"
    v=pcrel(a)
    return (v+((a+4+ (2 if True else 0))&~3))&0xffffffff
# 精确算 add 的地址
def chain2(ldr_a, add_a):
    v=pcrel(ldr_a)
    return (v + ((add_a+4)&~3)) & 0xffffffff
print()
print("=== 关键字符串/全局 ===")
def show(tag, addr, kind='str'):
    if kind=='str':
        print("  %-28s @0x%08x  \"%s\"" % (tag, addr, cstr(addr)))
    else:
        print("  %-28s @0x%08x  = 0x%x" % (tag, addr, lit(addr)))
show("r4 (两个 std::string 默认值)", chain2(0xec0aa,0xec0b8))
show("r2 (0xec04c) log fmt",            chain2(0xec04c,0xec05a))
show("r7 (body 键名)",                 chain2(0xec050,0xec064))
gbase_base = chain2(0xec054,0xec068)
show("r6 (GOT 基准)", gbase_base, 'num')
show("fp (元素键名)",                  chain2(0xec10c,0xec11e))
show("sp+0x10 (元素键名2?)",           chain2(0xec112,0xec122))
show("sp+0x24 (servoNum 候选1)",       chain2(0xec120,0xec128))
show("sp+0x30 (servoNum 候选2)",       chain2(0xec12c,0xec12e))
show("候选3 (0xec2be)",                chain2(0xec2be,0xec2c4))
show("候选4 (0xec2d6)",                chain2(0xec2d6,0xec2dc))
show("候选5 (0xec352)",                chain2(0xec352,0xec358))
show("候选6 (0xec372)",                chain2(0xec372,0xec378))
show("log@0xec296",                    chain2(0xec296,0xec29e))
show("log@0xec2f8",                    chain2(0xec2f8,0xec306))
show("log@0xec2fc",                    chain2(0xec2fc,0xec308))
print()
print("=== r6 基准 + 常量索引 -> GOT 槽 ===")
# gotmap
ds,dstr=S['.dynsym'],S['.dynstr']
def dynsym_name(idx):
    o=ds["offset"]+idx*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
    e=d.index(b"\x00", dstr["offset"]+nm)
    return d[dstr["offset"]+nm:e].decode("ascii","replace")
gotmap={}
rp=S['.rel.plt']
for i in range(rp["size"]//8):
    r_off,r_info=struct.unpack_from("<II", d, rp["offset"]+i*8)
    gotmap[r_off]=dynsym_name(r_info>>8)
# 库自有全局
st, sr = S['.symtab'], S['.strtab']
glob={}
for i in range(st["size"]//16):
    o=st["offset"]+i*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
    if nm==0 or shndx==0 or shndx>=len(secs): continue
    sec=secs[shndx]
    if sec["sname"] not in ('.bss','.data','.data.rel.ro'): continue
    e=d.index(b"\x00", sr["offset"]+nm)
    glob.setdefault(sec["addr"]+val, d[sr["offset"]+nm:e].decode("ascii","replace"))
GOT = gbase_base
for idx_at, desc in ((0xec096,'SDOWRCount 目标'),(0xec324,'AllSDOWRInfo 基址'),(0xec314,'状态全局'),
                     (0xec148,'COW 哨兵'),(0xec2f0,'COW 哨兵2'),(0xec0a4,'COW 哨兵0'),
                     (0xec240,'COW 哨兵3'),(0xec202,'COW 哨兵4'),(0xec210,'COW 哨兵5'),
                     (0xec22a,'COW 哨兵6'),(0xec104,'AllSDOWRInfo?'),(0xec108,'?')):
    v=pcrel(idx_at)
    tgt=(GOT+v)&0xffffffff
    nm=gotmap.get(tgt) or glob.get(tgt)
    print("  0x%06x idx=0x%-5x  槽=0x%08x  %-22s %s" % (idx_at, v, tgt, desc, nm or "(未登记)"))
# 【0xec0a4 的索引是 r3 而非直接 ldr】
print()
print("=== 检查 0xec094-0xec0b4 的 SDOWRCount 写入 ===")
for a in range(0xec094,0xec0b8,2):
    i=ins.get(a)
    if i: print("  0x%06x  %-7s %s" % (a,i.mnemonic,i.op_str))
