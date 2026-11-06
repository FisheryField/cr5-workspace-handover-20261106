
import json, datetime
data = open(r"D:\mydata\workspace\data\session_dump.jsonl","rb").read()
lines=[l for l in data.split(b"\n") if l.strip()]
lo = datetime.datetime(2026,9,23,16,14,0); hi = datetime.datetime(2026,9,23,16,32,0)
for l in lines:
    try: o=json.loads(l)
    except: continue
    t=o.get('time')
    if not t: continue
    d=datetime.datetime.fromtimestamp(t/1000)
    if not (lo<=d<=hi): continue
    ty=o.get('type')
    if ty not in ('user/message','assistant/message'): continue
    dd=o.get('data',{}); msg=dd.get('message',dd); role=msg.get('role','?')
    txts=[]
    for c in (msg.get('content') or []):
        if isinstance(c,dict) and c.get('type')=='text': txts.append(c.get('text',''))
    s="\n".join(txts).strip()
    if not s: continue
    print("="*88)
    print("[%s] %s" % (d.strftime("%H:%M:%S"), role))
    print(s[:1800])
