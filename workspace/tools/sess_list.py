
import os, glob, json, datetime, sys
base = r"C:\Users\FisheryField\.dsh\sessions"
if not os.path.isdir(base):
    print("NOT FOUND:", base); sys.exit()
ds = [d for d in os.listdir(base) if 'mydata-workspace' in d]
print("会话目录:", ds)
for d in ds:
    p = os.path.join(base, d)
    for root,_,files in os.walk(p):
        for f in files:
            fp = os.path.join(root,f)
            print("  %-60s %d bytes  mtime=%s" % (f, os.path.getsize(fp),
                  datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime('%m-%d %H:%M:%S')))
