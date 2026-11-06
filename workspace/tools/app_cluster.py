
import re
d = open(r"D:\mydata\workspace\data\Application.app",'rb').read()
# Thumb-2 ldr.w Rt,[Rn,#imm12] = F8D? <Rt<<12|imm12>, 小端字节: F8 D? lo(imm12) hi
def cluster(name, base):
    # 在 base 处找 F8 D? ..
    pat = re.compile(rb'\xf8\xd[\x00-\xff]')
    hits = []
    for m in re.finditer(pat, d):
        o = m.start()
        if o+4 > len(d): continue
        hw2 = d[o+2] | (d[o+3]<<8)
        imm = hw2 & 0xfff
        if imm == base:
            hits.append((o, (hw2>>12)&0xf))
    return hits
print("=== 各偏移的 ldr.w x,[y,#off] 出现次数 ===")
offs = {0x4c4:None,0x4c8:None,0x4cc:None,0x4d0:None,0x4d4:None,0x4dc:None}
allhits={}
for k in offs:
    h = cluster(k,k)
    allhits[k]=[x[0] for x in h]
    print("   0x%03x : %d 处  样例: %s" % (k, len(h), [hex(x[0]) for x in h[:6]]))
print()
print("=== 找成簇的位置（多个不同偏移在 4KB 窗口内）===")
best=[]
for a in allhits[0x4c4]:
    near=set()
    for k,v in allhits.items():
        for b in v:
            if abs(b-a) < 4096: near.add(k); break
    if len(near)>=3: best.append((a, sorted(near)))
seen=set()
for a,near in best:
    key=a//4096
    if key in seen: continue
    seen.add(key)
    print("   0x%06x 附近出现: %s" % (a, [hex(x) for x in near]))
print("   簇数 = %d" % len(seen))
