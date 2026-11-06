
d = open(r"D:\mydata\workspace\data\Application.app",'rb').read()
def scan(base):
    out=[]
    for o in range(0, len(d)-4, 2):
        if d[o] != 0xF8: continue
        if (d[o+1] & 0xF0) != 0xD0: continue
        hw2 = d[o+2] | (d[o+3]<<8)
        if (hw2 & 0xfff) == base:
            out.append((o, (hw2>>12)&0xf))
    return out
res={}
print("=== ldr.w Rt,[Rn,#off] 出现次数 ===")
for k in (0x4c4,0x4c8,0x4cc,0x4d0,0x4d4,0x4dc):
    h=scan(k); res[k]=[x[0] for x in h]
    print("   0x%03x : %-3d 处  样例 %s" % (k,len(h),[hex(x) for x in h[:8]]))
print()
print("=== 成簇检测: 4KB 窗口内至少命中 3 个不同偏移 ===")
seen=set(); n=0
for a in res[0x4c4]:
    near=[k for k in res if any(abs(b-a)<4096 for b in res[k])]
    if len(near)>=3:
        blk=a//4096
        if blk in seen: continue
        seen.add(blk); n+=1
        if n<=12:
            print("   0x%06x 窗口内命中: %s" % (a, [hex(k) for k in near]))
print("   簇数 = %d" % n)
