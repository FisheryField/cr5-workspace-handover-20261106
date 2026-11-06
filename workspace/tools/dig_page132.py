# -*- coding: utf-8 -*-
import pathlib, struct, re, collections

D = pathlib.Path(r"D:\mydata\workspace\data\captures\zero_shm_20260923_112646\zero_shm_20260923_112646")
base = (D/"base"/"R6.bin").read_bytes()
cur  = (D/"cur"/"R6.bin").read_bytes()
print(f"region6: base={len(base):,} cur={len(cur):,}")

# 只在 page 132/133 上找差异
for pg in (132, 133, 64, 65):
    o0 = pg*4096; o1 = o0+4096
    a = base[o0:o1]; b = cur[o0:o1]
    diff = [i for i in range(4096) if a[i] != b[i]]
    print(f"\n===== page {pg}（region6 绝对 0x{0x73a00000+o0:08X}）差异 {len(diff)} 字节 =====")
    if not diff: continue
    lo, hi = min(diff), max(diff)
    print(f"  差异区间页内 0x{lo:X}–0x{hi:X}")
    # 以 40 字节为步长扫，找 float 数组
    print("  --- 页内 0xE00–0xF40 的 float32（步长 4，每行 8 个）---")
    for off in range(0xE00, 0xF40, 32):
        fa = struct.unpack_from("<8f", a, off)
        fb = struct.unpack_from("<8f", b, off)
        mark = "  <<< 变化" if any(x!=y for x,y in zip(a[off:off+32], b[off:off+32])) else ""
        print(f"   +0x{off:03X} base: " + " ".join(f"{v:>12.4f}" for v in fa) + mark)
        if mark:
            print(f"          cur : " + " ".join(f"{v:>12.4f}" for v in fb))
