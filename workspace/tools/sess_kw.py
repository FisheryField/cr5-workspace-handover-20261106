
import json, datetime, sys
data = open(r"D:\mydata\workspace\data\session_dump.jsonl","rb").read()
lines = [l for l in data.split(b"\n") if l.strip()]
def ts(ms): return datetime.datetime.fromtimestamp(ms/1000).strftime("%m-%d %H:%M:%S")
# 1) 找所有提到 伺服参数 的条目
KW = ["伺服参数","servoParam","readServoParams","modifyServoParams","维护工具","RobotMaintenance","servoReadOnlyAddress","H01.17"]
print("========== 命中关键词的条目 ==========")
n=0
for i,l in enumerate(lines):
    s = l.decode('utf-8','replace')
    if any(k in s for k in KW):
        try: o=json.loads(l)
        except: continue
        t = o.get('time')
        tt = ts(t) if t else "?"
        txt = s
        # 精简
        if len(txt)>260: txt = txt[:260]+"…"
        print("[%s] 行%d %s" % (tt, i, txt))
        n+=1
        if n>45: print("…(截断)"); break
