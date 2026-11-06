import re
data = open("libdataSvr.so.bin","rb").read()
# find the route registration in DataSubProcess constructor: look for "exchange" as URI part
for m in re.finditer(rb"exchange", data, re.IGNORECASE):
    i = m.start()
    ctx = data[max(0,i-60):i+60]
    # printable context
    txt = re.sub(rb"[^\x20-\x7e]", b".", ctx).decode()
    if "/" in txt or "Exchange" in txt:
        print(hex(i), txt)
