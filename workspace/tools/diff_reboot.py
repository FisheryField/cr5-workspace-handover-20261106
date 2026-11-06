# -*- coding: utf-8 -*-
"""断电前后 10MB 共享段的完整差异分析。"""
import pathlib, struct, collections

R = pathlib.Path(r"D:\mydata\workspace\data\reboot_probe")
A = R/"zp_20260923_113642_before"; B = R/"zp_20260923_113642_after"
a = (A/"seg_full.bin").read_bytes(); b = (B/"seg_full.bin").read_bytes()
print(f"段大小 A={len(a):,} B={len(b):,}")

diff = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
pages = collections.Counter(i//4096 for i in diff)
print(f"\n差异字节 {len(diff):,}，涉及 {len(pages)} 个 4KB 页")
print("差异最多的页（页号:字节数）：")
for p, c in pages.most_common(20):
    print(f"   page {p:<5} {c:>6} 字节   绝对 0x{0x73A00000 + p*4096:08X}")

# 页 64 / 132 的 6 条记录（两个字段）
print("\n=== page 132 @0xE24：6 条 40 字节记录（字段0 / 字段1）===")
for tag, d in (("断电前", a), ("断电后", b)):
    o = 132*4096
    print(f"  {tag}:")
    for i in range(6):
        f0 = struct.unpack_from("<f", d, o+0xE24+40*i)[0]
        f1 = struct.unpack_from("<f", d, o+0xE2C+40*i)[0]
        print(f"     轴{i+1}  {f0:>13.4f}   {f1:>13.4f}")

print("\n=== page 64 @0xE24 同样结构 ===")
for tag, d in (("断电前", a), ("断电后", b)):
    o = 64*4096
    v = [struct.unpack_from("<f", d, o+0xE24+40*i)[0] for i in range(6)]
    v1 = [struct.unpack_from("<f", d, o+0xE2C+40*i)[0] for i in range(6)]
    print(f"  {tag}: f0={[round(x,3) for x in v]}")
    print(f"          f1={[round(x,3) for x in v1]}")

# 差异页里，哪些是"只在某一侧有值"
print("\n=== 差异页的填充情况（A有值/B全零 之类）===")
for p, c in pages.most_common(12):
    o = p*4096
    na = sum(1 for x in a[o:o+4096] if x); nb = sum(1 for x in b[o:o+4096] if x)
    print(f"   page {p:<5} A非零={na:<5} B非零={nb:<5} 差异={c}")
