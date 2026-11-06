
import os, glob, csv, io
roots = [r"D:\software\dobot\V1.3.4-stable\upgradeFiles",
         r"D:\mydata\workspace\data\official",
         r"D:\mydata\workspace\data\cabinet"]
found=[]
for r in roots:
    if not os.path.isdir(r): continue
    for root,_,files in os.walk(r):
        for f in files:
            if f.lower().endswith('.csv'):
                p=os.path.join(root,f)
                found.append((p, os.path.getsize(p)))
print("=== 找到的 CSV ===")
for p,s in found: print("  %-100s %d" % (p,s))
