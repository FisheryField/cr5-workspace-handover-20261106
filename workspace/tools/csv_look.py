
import csv, io, sys
for name in ('param.csv','J6.csv'):
    p = r'D:\mydata\workspace\data\official\servoCSV' + '\\' + name
    raw = open(p,'rb').read()
    for enc in ('gbk','utf-8'):
        try:
            txt = raw.decode(enc); break
        except Exception: continue
    print("="*70)
    print("FILE %s   (%s)  %d bytes" % (name, enc, len(raw)))
    rows = list(csv.reader(io.StringIO(txt)))
    print("rows=%d  cols=%d" % (len(rows), len(rows[0]) if rows else 0))
    print("HEADER:", rows[0])
    for r in rows[1:4]:
        print("  ", r)
    # 找编码器校零相关
    print("--- 含 '编码器' 或 '校零' 或 '零点' 或 '位置角' 的行 ---")
    for i,r in enumerate(rows):
        joined = ','.join(r)
        if any(k in joined for k in ('编码器','校零','零点','位置角')):
            print("  [%d] %s" % (i, joined[:200]))
