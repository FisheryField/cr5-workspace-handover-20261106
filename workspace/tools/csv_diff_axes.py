
import csv, io, os
base = r"D:\software\dobot\V1.3.4-stable\upgradeFiles\3.5.6\3.5.6.1\servoCSV\CR"
def load(p):
    txt = open(p,'rb').read().decode('gbk', errors='replace')
    return list(csv.reader(io.StringIO(txt)))
j1 = load(os.path.join(base,"CR5","J1.csv"))
j6 = load(os.path.join(base,"CR5","J6.csv"))
print("J1.csv 行数=%d   J6.csv 行数=%d" % (len(j1), len(j6)))
print("--- J1.csv 前 8 行 ---")
for r in j1[:8]: print("   ", [c for c in r if c][:8])
print()
print("--- KeyParameter.csv ---")
kp = open(r"D:\software\dobot\V1.3.4-stable\upgradeFiles\KeyParameter.csv",'rb').read().decode('gbk',errors='replace')
print(kp[:900])
print()
# 按第一个非空列做 key 做 diff
def keyed(rows):
    d={}
    for r in rows:
        cells=[c for c in r if c.strip()]
        if not cells: continue
        d[cells[0]] = cells
    return d
a=keyed(j1); b=keyed(j6)
print("=== J1 vs J6 差异行 ===")
n=0
for k in a:
    if k in b and a[k]!=b[k]:
        print("  J1: %-70s" % str(a[k])[:110])
        print("  J6: %-70s" % str(b[k])[:110])
        n+=1
        if n>25: print("  ...(截断)"); break
print("差异数(截至截断) =", n)
