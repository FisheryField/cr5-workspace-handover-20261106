
import struct
d = open(r"D:\mydata\workspace\data\Application.app",'rb').read()
print("前 32 字节:", d[:32].hex(' '))
print("是否 ELF:", d[:4]==b'\x7fELF')
if d[:4]==b'\x7fELF':
    print("  class=%d data=%d machine=%d type=%d" % (d[4],d[5],struct.unpack_from("<H",d,18)[0],struct.unpack_from("<H",d,16)[0]))
# 找可识别的 CODESYS 头
for tag in (b'CODESYS', b'3S -', b'Smart Software', b'.app', b'ARM', b'Thumb'):
    i=d.find(tag)
    print("  %-20s @ %s" % (tag.decode(), hex(i) if i>=0 else "无"))
# 统计 F8 D? 字节对（Thumb-2 ldr.w 前缀）
n=sum(1 for o in range(len(d)-1) if d[o]==0xF8 and (d[o+1]&0xF0)==0xD0)
print("  F8 D? 出现次数:", n)
m=sum(1 for o in range(len(d)-1) if d[o]==0xE5 or d[o]==0xE9 or d[o]==0xE3 or d[o]==0xE1)
print("  ARM 常见首字节 E1/E3/E5/E9 出现次数:", m)
# .text 大小线索
i=d.find(b'\x7fELF')
print("  文件里第一个 ELF 魔数位置:", hex(i) if i>=0 else "无")
