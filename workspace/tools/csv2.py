
import csv, io, collections
p = r"D:\software\dobot\V1.3.4-stable\upgradeFiles\servoParamTemplate\CR_Param.csv"
txt = open(p,'rb').read().decode('gbk', errors='replace')
rows = list(csv.reader(io.StringIO(txt)))
# 找真正的表头（含 ParaIndex/ParaMapIndex）
hdr_i = None
for i,r in enumerate(rows[:12]):
    j=','.join(r)
    if 'ParaIndex' in j or 'ParaMapIndex' in j:
        hdr_i = i; break
print("表头行号 =", hdr_i)
if hdr_i is not None:
    print("表头 =", [c for c in rows[hdr_i] if c])
    hdr = rows[hdr_i]
    data = [r for r in rows[hdr_i+1:] if len(r)>3 and r[1]]
    print("数据行 =", len(data))
    # 找列
    try:
        ci = hdr.index('ParaIndex'); cm = hdr.index('ParaMapIndex')
        cn = hdr.index('ParaName') if 'ParaName' in hdr else None
    except Exception as e:
        ci,cm,cn = 3,2,None
    print()
    # 按组名分组
    grp = collections.OrderedDict()
    for r in data:
        g = r[1] if len(r)>1 else '?'
        grp.setdefault(g, []).append(r)
    print("组数 =", len(grp))
    for g, rs in grp.items():
        print("  %-28s %3d 项   例: %s" % (g, len(rs), ' | '.join(x[ci] for x in rs[:4])))
