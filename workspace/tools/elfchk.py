
import struct
d=open(r"D:\mydata\workspace\ecat_mbx.exe",'rb').read()
assert d[:4]==b'\x7fELF'
ei_class=d[4]; ei_data=d[5]
etype,emach,ever = struct.unpack_from("<HHH", d, 16)
print("class=%d (1=32bit)  data=%d (1=LE)  type=%d (2=EXEC)  machine=%d (40=ARM)  version=%d"%(ei_class,ei_data,etype,emach,ever))
e_flags, = struct.unpack_from("<I", d, 36)
print("e_flags=0x%08X   EF_ARM_EABI_VER5=0x05000000 -> %s" % (e_flags, "EABI5 OK" if (e_flags>>24)==5 else "??"))
print("  hard-float flag(0x400)=%s" % bool(e_flags & 0x400))
# program headers
e_phoff,=struct.unpack_from("<I",d,28); e_phentsize,e_phnum=struct.unpack_from("<HH",d,42)
print("program headers: %d" % e_phnum)
for i in range(e_phnum):
    o=e_phoff+i*e_phentsize
    p_type,p_offset,p_vaddr,p_paddr,p_filesz,p_memsz,p_flags,p_align=struct.unpack_from("<IIIIIIII",d,o)
    print("  type=%d off=0x%06x vaddr=0x%08x filesz=%-8d memsz=%-8d flags=%d" % (p_type,p_offset,p_vaddr,p_filesz,p_memsz,p_flags))
# 动态段？
import re
print("INTERP:", re.findall(rb'ld-[a-z0-9\.\-]+\.so[0-9\.]*', d[:4096]))
