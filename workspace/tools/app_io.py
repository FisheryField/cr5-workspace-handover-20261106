
import re
d = open(r"D:\mydata\workspace\data\Application.app",'rb').read()
print("=== 全部 Device.Application.* 符号（去重，按前缀归类）===")
syms=[]
seen=set()
for m in re.finditer(rb'Device\.Application\.[A-Za-z0-9_.]{1,80}', d):
    s=m.group().decode('latin-1')
    if s in seen: continue
    seen.add(s); syms.append((m.start(),s))
print("共 %d 个" % len(syms))
# 只打印 IoConfig_Globals 相关的完整列表
io=[x for x in syms if 'IoConfig_Globals' in x[1]]
print("\n--- IoConfig_Globals.* (%d 个) ---" % len(io))
for a,s in io[:120]:
    print("   0x%06x  %s" % (a, s))
print("\n--- 其它 Device.Application POU 级符号 ---")
for a,s in syms:
    if 'IoConfig_Globals' in s: continue
    if len(s.split('.'))<=4: print("   0x%06x  %s" % (a,s))
