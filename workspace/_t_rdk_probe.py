# -*- coding: utf-8 -*-
"""探测 RoboDK .rdk 工作站文件的存储格式，并定位内部 python 脚本的存法。"""
import io, os, re, struct, sys, zlib

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\2026-9-7.rdk'
raw = open(P, 'rb').read()
print('文件大小 =', len(raw))
print('前16字节 =', raw[:16].hex(' '))

# 1) 尝试 zlib 解压：偏移 0/4/5
for off in (0, 4, 5):
    try:
        d = zlib.decompressobj().decompress(raw[off:])
        print('zlib@%-2d OK 解出 %d 字节' % (off, len(d)))
        out = P + '.unz_%d.bin' % off
        open(out, 'wb').write(d)
        print('  写出', out)
        print('  解压后前 64 字节 =', d[:64].hex(' '))
        print('  解压后前 64 ascii =', ''.join(chr(c) if 32 <= c < 127 else '.' for c in d[:64]))
        break
    except Exception as e:
        print('zlib@%-2d 失败: %s' % (off, e))

# 2) 头部 4 字节含义
print('头 4 字节 LE u32 =', struct.unpack_from('<I', raw, 0)[0], ' BE u32 =', struct.unpack_from('>I', raw, 0)[0])
