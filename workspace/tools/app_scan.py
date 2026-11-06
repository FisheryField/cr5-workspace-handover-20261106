
import re
P = r"D:\mydata\workspace\data\Application.app"
d = open(P,'rb').read()
print("大小 %d" % len(d))
KW = ['sdo','SDOWR','servoParam','readServoParams','modifyServoParams','addr%x','AllSDOWR','IsExistSDO',
      'Mailbox','MAILBOX','ethercat','EtherCAT','CoE','0x2001','servoParams.json']
print("=== 关键词命中 ===")
seen=set()
for m in re.finditer(rb'[\x20-\x7e]{3,140}', d):
    s=m.group().decode('latin-1')
    low=s.lower()
    for k in KW:
        if k.lower() in low:
            if s in seen: break
            seen.add(s)
            print("   0x%06x  %s" % (m.start(), s[:130]))
            break
print()
print("=== 找 16 位常量 0x4c4 / 0x4c8 / 0x4cc / 0x4d0 / 0x4d4 / 0x4dc 的字节序列 ===")
import struct
for name,val in (('0x4c4',0x4c4),('0x4c8',0x4c8),('0x4cc',0x4cc),('0x4d0',0x4d0),('0x4d4',0x4d4),('0x4dc',0x4dc)):
    b=struct.pack('<H',val)
    idxs=[m.start() for m in re.finditer(re.escape(b), d)]
    print("   %s (LE %s) : %d 处" % (name, b.hex(), len(idxs)))
# 看 0x4c4 出现处的上下文
b=struct.pack('<H',0x4c4)
for m in list(re.finditer(re.escape(b), d))[:6]:
    o=m.start()
    print("   0x%06x 前後: %s" % (o, d[max(0,o-16):o+16].hex(' ')))
