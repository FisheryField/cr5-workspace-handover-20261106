
import json, datetime
data = open(r"D:\mydata\workspace\data\session_dump.jsonl","rb").read()
lines=[l for l in data.split(b"\n") if l.strip()]
def ts(ms): return datetime.datetime.fromtimestamp(ms/1000)
lo = datetime.datetime(2026,9,23,16,5,0); hi = datetime.datetime(2026,9,23,16,35,0)
out=[]
for i,l in enumerate(lines):
    try: o=json.loads(l)
    except: continue
    t=o.get('time')
    if not t: continue
    d=ts(t)
    if not (lo<=d<=hi): continue
    ty=o.get('type')
    if ty not in ('user/message','assistant/message'): continue
    dd=o.get('data',{})
    msg=dd.get('message',dd)
    role=msg.get('role','?')
    txts=[]
    for c in (msg.get('content') or []):
        if isinstance(c,dict):
            if c.get('type')=='text': txts.append(c.get('text',''))
            elif c.get('type')=='reasoning': txts.append('[推理] '+c.get('text','')[:200])
    s="\n".join(txts)
    if not s.strip(): continue
    out.append((d,role,s))
print("窗口内消息 %d 条" % len(out))
for d,role,s in out:
    print("="*90)
    print("[%s] %s" % (d.strftime("%H:%M:%S"), role))
    print(s[:1400])
