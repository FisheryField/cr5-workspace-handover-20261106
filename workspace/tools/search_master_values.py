#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在【最新】TxPDO 映像里搜主控读到的那一项：float32 / float64 / int32 三种编码都试。"""
import io
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\workspace\data\txpdo_fresh.bin'
d = io.open(P, 'rb').read()
print('dump = %d 字节' % len(d))

# 版本字定位
hits = []
i = d.find(b'\xd8\x32')
while i >= 0:
    hits.append(i)
    i = d.find(b'\xd8\x32', i + 1)
print('版本字 0x32D8 命中 %d 处: %s' % (len(hits), ' '.join('0x%05X' % h for h in hits)))
print('')

values = {
    '主控J2=365.3275': 365.327554,
    '实际J2=243.2175': 243.217468,
    '主控J1=10.7583': 10.758300,
    '实际J1=40.1315': 40.131492,
    '主控J5=-11.1240': -11.124022,
    '主控J3=9.4161': 9.416075,
    '实际J6=106.0424': 106.042411,
}
for label, v in values.items():
    print('=== %s ===' % label)
    for name, fmt, tol in (('float64', '<d', 1e-4), ('float32', '<f', 1e-3)):
        found = []
        size = struct.calcsize(fmt)
        for off in range(0, len(d) - size):
            try:
                x = struct.unpack_from(fmt, d, off)[0]
            except Exception:  # noqa: BLE001
                continue
            if abs(x - v) <= tol:
                found.append(off)
                if len(found) >= 6:
                    break
        print('   %-8s 命中 %d 处: %s' % (name, len(found), ' '.join('0x%05X' % o for o in found)))
    print('')
