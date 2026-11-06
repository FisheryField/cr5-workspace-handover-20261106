# -*- coding: utf-8 -*-
import pathlib, struct, collections
R = pathlib.Path(r"D:\mydata\workspace\data\reboot_probe")
a = (R/"zp_20260923_113642_before"/"seg_full.bin").read_bytes()
b = (R/"zp_20260923_113642_after"/"seg_full.bin").read_bytes()
for pg in (133, 65, 64):
    o = pg*4096
    d = [i for i in range(4096) if a[o+i] != b[o+i]]
    print(f"\n===== page {pg}（绝对 0x{0x73A00000+o:08X}）差异 {len(d)} 字节，页内范围 0x{min(d):X}–0x{max(d):X} =====")
    # 按 4 字节对齐分组，打印 float 前后
    words = sorted(set(i - i%4 for i in d))
    print(f"  涉及 {len(words)} 个 32 位字：")
    for w in words[:26]:
        fa = struct.unpack_from("<f", a, o+w)[0]; fb = struct.unpack_from("<f", b, o+w)[0]
        ia = struct.unpack_from("<i", a, o+w)[0]; ib = struct.unpack_from("<i", b, o+w)[0]
        s = f"   +0x{w:03X}  f32 {fa:>14.4f} -> {fb:>14.4f}"
        if abs(fa) < 1e-9 or abs(fb) < 1e-9 or abs(fa) > 1e4:
            s += f"   i32 {ia:>12} -> {ib:>12}"
        print(s)
