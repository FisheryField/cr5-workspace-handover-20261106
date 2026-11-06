# -*- coding: utf-8 -*-
"""对比断电前后其余共享段，并检查是否有"未被清除的备份"藏着零点数据。"""
import pathlib, struct, collections

R = pathlib.Path(r"D:\mydata\workspace\data\reboot_probe")
A = R/"zp_20260923_113642_before"; B = R/"zp_20260923_113642_after"

names = sorted(set(f.name for f in A.glob("seg_*.bin")))
print("对比的段:", names)

for nm in names:
    a = (A/nm).read_bytes(); b = (B/nm).read_bytes()
    d = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    na, nb = sum(1 for x in a if x), sum(1 for x in b if x)
    print(f"\n### {nm}  {len(a):,} B")
    print(f"    A非零={na:,}  B非零={nb:,}   差异={len(d):,} 字节")
    if d:
        pages = collections.Counter(i//4096 for i in d)
        print("    差异页: " + ", ".join(f"p{p}({c})" for p, c in pages.most_common(8)))
        # 看差异内容
        for w in sorted(set(i - i%4 for i in d))[:10]:
            fa = struct.unpack_from("<f", a, w)[0]; fb = struct.unpack_from("<f", b, w)[0]
            ia = struct.unpack_from("<i", a, w)[0]; ib = struct.unpack_from("<i", b, w)[0]
            print(f"      +0x{w:05X} f32 {fa:>14.4f} -> {fb:>14.4f}   i32 {ia} -> {ib}")

# 关键验证：断电前 page132 f1 的值，是否在"任何一处 A 侧数据"里、且在 B 侧也被清掉了
print("\n\n=== 检查：断电前 f1 = [-17.5, 875, 70, 98, 47.6, 28.0]，在哪些地方能找到同样的值 ===")
target = [-17.5, 875.0, 70.0, 98.0, 47.6, 28.0]
def scan(path, label):
    d = pathlib.Path(path).read_bytes()
    hits = []
    for off in range(0, len(d)-4, 4):
        v = struct.unpack_from("<f", d, off)[0]
        for t in target:
            if t != 0 and abs(v - t) < 1e-4:
                hits.append((hex(off), t)); break
    print(f"  {label}: {len(hits)} 处 -> {hits[:12]}")
scan(A/"seg_full.bin", "A 10MB段")
scan(B/"seg_full.bin", "B 10MB段")
for nm in names:
    scan(A/nm, "A " + nm)
