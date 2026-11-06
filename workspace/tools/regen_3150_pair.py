#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 3.1.5.hex 重新生成固件 FoE 包（并核验），同时归档配套 XML。
   事实依据：
     · 固件 = hex 的 0x08010000 起应用区 + 0x20 字节厂商 FoE 头
     · XML  = ESC EEPROM 映像（MCU flash 里没有），沿用厂商 CR_Servo_ST_XML_V3.0.0.bin
"""
import hashlib
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HEX = r'D:\mydata\working things\机械臂控制柜数据\3.1.5.hex'
XMLSRC = r'D:\mydata\workspace\data\official\pkg\CR_Servo_ST_XML_V3.0.0.bin'
REFBIN = r'D:\mydata\workspace\data\servo_fw_samples\CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin'
OUTDIR = r'D:\mydata\workspace\servo_fw\pair_3150'
FWOUT = os.path.join(OUTDIR, 'CR5_Servo_ST_FOE_V3.1.5.0_FROM_HEX.bin')
XMLOUT = os.path.join(OUTDIR, 'CR_Servo_ST_XML_V3.0.0.bin')

img = bytearray(b'\xff' * 0x100000)
base = 0
with open(HEX, 'r', errors='replace') as f:
    for line in f:
        line = line.strip()
        if not line.startswith(':'):
            continue
        raw = bytes.fromhex(line[1:])
        n, addr, typ = raw[0], (raw[1] << 8) | raw[2], raw[3]
        data = raw[4:4 + n]
        if typ == 0x00:
            img[(base + addr) - 0x08000000:(base + addr) - 0x08000000 + n] = data
        elif typ == 0x01:
            break
        elif typ == 0x02:
            base = int.from_bytes(data, 'big') << 4
        elif typ == 0x04:
            base = int.from_bytes(data, 'big') << 16

# 应用区终点 = 最后一个非 FF 字节（与原始候选包口径一致）
end = len(img) - 1
while end > 0x10000 and img[end] == 0xFF:
    end -= 1
payload = bytes(img[0x10000:end + 1])
print('hex 应用区: 0x08010000..0x%08X  共 %d 字节' % (0x08000000 + end, len(payload)))

# 合成 0x20 字节厂商 FoE 头
md5 = hashlib.md5(payload).digest()
hdr = bytearray(0x20)
hdr[0:4] = bytes.fromhex('d4c3b2a1')
hdr[4:16] = md5[:12]
hdr[16:20] = md5[12:16]
hdr[20:24] = struct.pack('<I', len(payload))
hdr[24:28] = struct.pack('<I', 8)   # 分类字段 = 小端 u32 8  ⇒ 08 00 00 00
                                    # （厂商 D8 包头同处也是 08000000；写反成 00000008 会差 2 字节）
hdr[28:32] = b'\xff\xff\xff\xff'
pkg = bytes(hdr) + payload

os.makedirs(OUTDIR, exist_ok=True)
open(FWOUT, 'wb').write(pkg)
print('')
print('已生成固件包: %s' % FWOUT)
print('  %d 字节, md5=%s' % (len(pkg), hashlib.md5(pkg).hexdigest()))
print('  头: %s' % pkg[:0x20].hex(' '))
print('  payload md5 = %s' % hashlib.md5(payload).hexdigest())

# 与已验证的包对照
if os.path.exists(REFBIN):
    ref = open(REFBIN, 'rb').read()
    print('')
    print('与已验证包 %s 比较:' % os.path.basename(REFBIN))
    print('  参考 %d 字节 md5=%s' % (len(ref), hashlib.md5(ref).hexdigest()))
    print('  差异字节数 = %d  %s' % (sum(1 for a, b in zip(pkg, ref) if a != b) if len(pkg) == len(ref) else -1,
                                     '✓ 完全一致' if pkg == ref else '✗ 不一致'))

# 归档 XML（ESC EEPROM 映像，MCU flash 里没有 ⇒ 只能用厂商原件）
if os.path.exists(XMLSRC):
    x = open(XMLSRC, 'rb').read()
    open(XMLOUT, 'wb').write(x)
    print('')
    print('已归档配套 XML: %s' % XMLOUT)
    print('  %d 字节, md5=%s（= 厂商 CR_Servo_ST_XML_V3.0.0.bin）' % (len(x), hashlib.md5(x).hexdigest()))
    print('  说明: 内容为 EtherCAT 从站 ESC EEPROM 映像（设备描述 + PDO/SM 配置），')
    print('        不在 MCU 应用 flash 内，故无法从 3.1.5.hex 提取 ✗')
