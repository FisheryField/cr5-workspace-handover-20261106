import struct, re
d = open("libdataSvr.so.bin","rb").read()
(_t,_m,_v,_e,_ph,shoff,_f,_eh,_pe,_pn,shentsize,shnum,shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
secs=[]
for i in range(shnum):
    f = struct.unpack_from("<IIIIIIIIII", d, shoff+i*shentsize)
    secs.append(dict(name_off=f[0],type=f[1],addr=f[3],offset=f[4],size=f[5],link=f[6],entsize=f[9]))
# find symbol protoExchange
target=None
for s in secs:
    if s["type"] not in (2,11): continue
    strt=secs[s["link"]]; base=strt["offset"]
    n=s["size"]//(s["entsize"] or 16)
    for i in range(n):
        off=s["offset"]+i*16
        (nm,info,other,shndx,val,size)=struct.unpack_from("<IIIBBH", d, off)
        name=d[base+nm:d.find(b"\0",base+nm)].decode("utf-8","replace")
        if "protoExchange" in name:
            target=(name,val&~1,size)
            print("SYM", hex(val), hex(size), name)
# dump strings referenced via PC-relative literals within the function
if target:
    name,val,size=target
    # find .text section containing val
    for s in secs:
        if s["type"]==1 and s["addr"]<=val<s["addr"]+s["size"]:
            fo=s["offset"]+(val-s["addr"])
            body=d[fo:fo+size]
            print("body at file", hex(fo), "size", size)
            break
    # find .rodata-ish section for literals
    lits=[]
    for s in secs:
        if s["type"]==1 and s["addr"]!=0 and s["size"]:
            pass
    # brute: scan body for ldr rX,[pc,#imm] is hard without disasm; instead print all 4-byte words that look like pointers into rodata
    for off in range(0,len(body)-3,4):
        w=struct.unpack_from("<I", body, off)[0]
        # map addr->file offset
        for s in secs:
            if s["type"]==1 and s["addr"]!=0 and s["addr"]<=w<s["addr"]+s["size"] and s["flags"] or False:
                pass
    print("(literal scan skipped)")
