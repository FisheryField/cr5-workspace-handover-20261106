
import csv, io
p = r'D:\software\dobot\V1.3.4-stable\upgradeFiles\servoParamTemplate\CR_Param.csv'
raw=open(p,'rb').read()
for enc in ('gbk','utf-8'):
    try: txt=raw.decode(enc); break
    except Exception: continue
rows=list(csv.reader(io.StringIO(txt)))
print("rows=%d cols=%d" % (len(rows), len(rows[0])))
hdr=rows[1]
print("表头:", [(i,h) for i,h in enumerate(hdr) if h])
print()
for r in rows:
    if len(r)>3 and r[3] in ('H01.17','H01.14','H01.15','H0C.02','H00.00','H01.00'):
        print("--- %s ---" % r[3])
        for i,h in enumerate(hdr):
            v = r[i] if i < len(r) else ''
            if h and v: print("   %-18s = %s" % (h, v[:60]))
        print()
print("=== 检查是否有任何列含 2000/2001 之类的地址 ===")
import re
for r in rows[2:6]:
    for i,v in enumerate(r):
        if re.match(r'^2\d{5}$', v.strip()):
            print("   row %s col %d(%s) = %s" % (r[3], i, hdr[i] if i<len(hdr) else '?', v))
