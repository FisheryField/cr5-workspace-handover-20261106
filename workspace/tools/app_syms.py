
import re
d = open(r"D:\mydata\workspace\data\Application.app",'rb').read()
KW = ('sdo','SDO','servo','Servo','param','Param','mbx','Mbx','MBX','mailbox','Mailbox','ethercat','EtherCAT',
      'axis','Axis','Dobot','dobot','robot','Robot','zero','Zero','calib','Calib','home','Home','encoder','Encoder')
print("=== 全文件里命中的符号/字符串 ===")
seen=set(); n=0
for m in re.finditer(rb'[\x20-\x7e]{4,120}', d):
    s=m.group().decode('latin-1')
    if any(k in s for k in KW):
        if s in seen: continue
        seen.add(s)
        print("   0x%06x  %s" % (m.start(), s[:110]))
        n+=1
        if n>70: print("   ...(截断)"); break
print()
print("=== 'Device.Application.' 开头的符号名 ===")
seen2=set(); k=0
for m in re.finditer(rb'Device\.Application\.[A-Za-z0-9_.]{1,60}', d):
    s=m.group().decode('latin-1')
    if s in seen2: continue
    seen2.add(s); k+=1
    if k<=60: print("   %s" % s)
print("   共 %d 个" % k)
