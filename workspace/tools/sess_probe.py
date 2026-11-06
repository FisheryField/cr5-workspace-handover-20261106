
import os, json, sys
base = r"C:\Users\FisheryField\.dsh\sessions"
hits=[]
for root,_,files in os.walk(base):
    for f in files:
        if f.endswith(".zstd"): hits.append(os.path.join(root,f))
for h in hits: print("FOUND:", h, os.path.getsize(h))
if not hits: sys.exit()
try:
    from compression import zstd
except Exception as e:
    print("no compression.zstd:", e); sys.exit()
data = zstd.decompress(open(hits[0],"rb").read())
lines = [l for l in data.split(b"\n") if l.strip()]
print("解压 %d 字节, %d 行" % (len(data), len(lines)))
for i in range(min(3,len(lines))):
    o=json.loads(lines[i])
    print("--- 行%d keys=%s" % (i, list(o.keys())))
    print("   ", json.dumps(o, ensure_ascii=False)[:300])
open(r"D:\mydata\workspace\data\session_dump.jsonl","wb").write(data)
print("已存 data/session_dump.jsonl")
