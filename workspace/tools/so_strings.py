
import re
p = r'D:\mydata\workspace\libdataSvr.so.bin'
d=open(p,'rb').read()
KEYS=[b'servoNum',b'key',b'readServoParams',b'modifyServoParams',b'parseAndReq',b'sdo',b'SDO',
      b'servoParams',b'driverParams',b'paramIndex',b'paramValue',b'slaveId',b'axis',b'index',
      b'SDOWR',b'AllSDOWRInfo',b'read sdo',b'write sdo',b'sdo read',b'sdo write',b'sdo info']
for k in KEYS:
    idxs=[m.start() for m in re.finditer(re.escape(k), d)]
    if not idxs: continue
    print("=== %-22r  x%d ===" % (k.decode(), len(idxs)))
    for i in idxs[:5]:
        a=max(0,i-40); b=min(len(d), i+80)
        raw=d[a:b]
        # 只显示可打印片段
        s=''.join(chr(c) if 32<=c<127 else '.' for c in raw)
        print("   @0x%06x  %s" % (i, s))
