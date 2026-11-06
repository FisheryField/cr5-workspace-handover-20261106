import re
data = open("libdataSvr.so.bin","rb").read()
# route table strings near "exchange" registrations in the constructor
for pat in [b"protocolExchange", b"/settings/exchange", b"exchange", b"servoParams"]:
    hits = [hex(m.start()) for m in re.finditer(re.escape(pat), data)]
    print(pat.decode(), "hits:", len(hits), hits[:12])
