#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用伺服固件补丁打包器（默认 dry-run）。

用法：
  python tools/mk_patch_pkg.py --base 3150 --spec patch.json [--write]
  # 或不写 json，直接内联：--addr 080249C4 --bytes f6ee000a [--addr ...]

spec.json 形如：
  { "tag": "rounding_port",
    "patches": [ {"addr": "080249C4", "bytes": "f6ee000a", "why": "…"}, … ] }

要点（本项目血泪）：
  * 地址用**真·flash 地址** = 0x08010000 + 文件偏移；基址由 3.1.5.hex / D8 hex 双重 100% 印证。
  * 补丁只写 **payload**（FoE 包的 0x20 字节之后），包壳按厂商布局重算 MD5。
  * 每个改动区都会用 capstone **反汇编回读**打印，人工确认解码无误（例如 NOP 必须写 `00 bf`）。
  * 默认 dry-run；加 --write 才落盘。
"""
import argparse
import binascii
import hashlib
import json
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASES = {
    '3150': os.path.join(ROOT, 'data', 'servo_fw_samples', 'CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin'),
    '328d8': os.path.join(ROOT, 'data', 'official', 'pkg', 'CR5_Servo_ST_FOE_V3.2.D.8.bin'),
}
LOAD = 0x08010000
HDR = 0x20

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
except ImportError:
    Cs = None


def disas(blob, addr, n=40):
    if Cs is None:
        return ['(capstone 不可用，跳过反汇编回读)']
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    out = []
    for ins in md.disasm(bytes(blob), addr):
        out.append('    %08x  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))
        if len(out) >= n:
            break
    return out or ['    (无法解码)']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='3150', choices=list(BASES))
    ap.add_argument('--spec', help='JSON 补丁清单')
    ap.add_argument('--addr', action='append', default=[], help='内联补丁地址(hex)')
    ap.add_argument('--bytes', action='append', default=[], help='内联补丁字节(hex)')
    ap.add_argument('--tag', default='patch')
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args()

    patches = []
    if a.spec:
        spec = json.load(open(a.spec, encoding='utf-8'))
        a.tag = spec.get('tag', a.tag)
        patches = [{'addr': p['addr'], 'bytes': p['bytes'], 'why': p.get('why', '')}
                   for p in spec['patches']]
    for ad, by in zip(a.addr, a.bytes):
        patches.append({'addr': ad, 'bytes': by, 'why': '(inline)'})
    if not patches:
        ap.error('需要 --spec 或 --addr/--bytes')

    path = BASES[a.base]
    d = bytearray(open(path, 'rb').read())
    payload = d[HDR:]
    print('基包 : %s' % os.path.basename(path))
    print('       文件 %d B，payload %d B，md5=%s' % (len(d), len(payload), hashlib.md5(d).hexdigest()))
    hdr_md5 = d[4:16].hex() + d[16:20].hex()
    print('       包头记录 payload MD5 = %s  实算 = %s  %s'
          % (hdr_md5, hashlib.md5(payload).hexdigest(),
             '✓' if hdr_md5 == hashlib.md5(payload).hexdigest() else '✗ 不一致(基包可疑)'))
    print('')

    ok = True
    for p in patches:
        addr = int(str(p['addr']), 16)
        new = bytes.fromhex(str(p['bytes']).replace(' ', ''))
        off = addr - LOAD
        if not (0 <= off < len(payload) - len(new)):
            print('!! %08X 越界 - STOP' % addr)
            ok = False
            continue
        old = bytes(payload[off:off + len(new)])
        payload[off:off + len(new)] = new
        print('== %08X (文件偏移 0x%X)  %s' % (addr, HDR + off, p.get('why', '')))
        print('   旧 : %s' % old.hex(' '))
        print('   新 : %s' % new.hex(' '))
        print('   改后反汇编（16 字节对齐起）：')
        start = off & ~1
        for line in disas(payload[start:start + 48], LOAD + start, 12):
            print(line)
        print('')
    if not ok:
        sys.exit(1)

    # 重算包壳
    body = bytes(payload)
    md5 = hashlib.md5(body).digest()
    hdr = bytearray(d[:HDR])
    hdr[4:16] = md5[:12]
    hdr[16:20] = md5[12:16]
    hdr[20:24] = struct.pack('<I', len(body))
    out = bytes(hdr) + body
    name = 'CR5_Servo_ST_FOE_V3.1.5.0_%s.bin' % a.tag if a.base == '3150' else \
           'CR5_Servo_ST_FOE_V3.2.D.8_%s.bin' % a.tag
    outp = os.path.join(ROOT, 'servo_fw', name)
    print('新包 : %s' % name)
    print('       大小 %d B，包头 %s' % (len(out), out[:HDR].hex(' ')))
    print('       新 payload MD5 = %s' % md5.hex())
    if not a.write:
        print('\nDRY RUN —— 未写盘（加 --write 落盘）')
        return 0
    open(outp, 'wb').write(out)
    print('\n已写：%s  (md5=%s)' % (outp, hashlib.md5(out).hexdigest()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
