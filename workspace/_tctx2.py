import re
data = open("libdataSvr.so.bin","rb").read()
for pat in [b"protoExchange", b"clear error from http exchange"]:
    for m in re.finditer(re.escape(pat), data):
        i = m.start()
        print("=== %s @ 0x%x ===" % (pat.decode(), i))
        win = data[max(0,i-1200):i+1200]
        for s in re.finditer(rb"[ -~]{6,}", win):
            print("  ", hex(max(0,i-1200)+s.start()), s.group().decode())
        break
