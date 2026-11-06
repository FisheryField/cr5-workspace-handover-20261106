
import struct
d = open(r"D:\mydata\workspace\data\Application.app",'rb').read()
def rec(tag, nameoff, stride):
    print("="*88)
    print("### %s  @0x%06x  步长=%d" % (tag, nameoff, stride))
    lo = nameoff-0x40
    for o in range(lo, nameoff+stride, 16):
        b=d[o:o+16]
        asc=''.join(chr(c) if 32<=c<127 else '.' for c in b)
        print("  %06x  %-47s  %s" % (o, b.hex(' '), asc))
    print("  -- 按 u32 解读 (记录起点 0x%06x) --" % nameoff)
    for i in range(0, 24):
        v,=struct.unpack_from("<I", d, nameoff-0x40+i*4)
        tag2=""
        if 0<v<0x20000000: tag2=" <小值>"
        print("     +%3d  0x%08x  %d%s" % (i*4-0x40, v, v, tag2))
rec("a1.config.write", 0x0e9f08, 0x8c)
rec("a1.config.read",  0x0ebd18, 0x88)
