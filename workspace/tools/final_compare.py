# -*- coding: utf-8 -*-
"""决定性对比：旧 main 块 vs 新采集同一地址范围的内容密度。"""
import tarfile, pathlib, struct, re

OLD = pathlib.Path(r"D:\mydata\codex\b\dobot-evidence-20260922\shm_focus32.tar.gz")
NEWD = pathlib.Path(r"D:\mydata\workspace\data\captures\zero_shm_20260923_112646\zero_shm_20260923_112646")

with tarfile.open(OLD, "r:gz") as t:
    om = {}
    for m in t.getmembers():
        b = m.name.split("/")[-1]
        if b in ("main_0.bin", "main_300.bin"):
            om[b] = t.extractfile(m).read()

old300 = om["main_300.bin"]
new_r6 = (NEWD/"base"/"R6.bin").read_bytes()
# 旧 main 基址 0x73A40000 -> region6 偏移 0x40000，长度 512 KB
slice_new = new_r6[0x40000:0x40000+len(old300)]

def nz(d): return sum(1 for x in d if x)
print(f"旧 main_300.bin       : {len(old300):,} B，非零 {nz(old300):,} ({nz(old300)*100//len(old300)}%)")
print(f"新 R6[0x40000:+512K]  : {len(slice_new):,} B，非零 {nz(slice_new):,} ({nz(slice_new)*100//len(slice_new)}%)")

same = sum(1 for i in range(len(old300)) if old300[i] == slice_new[i])
print(f"两者逐字节相同: {same:,} / {len(old300):,} ({same*100//len(old300)}%)")

print("\n--- 只看我们关心的那 40 字节（偏移 0x44E00–0x44E40）---")
for tag, d in (("旧 main_300", old300), ("新 R6(基线)", slice_new)):
    fa = struct.unpack_from("<16f", d, 0x44E00)
    print(f"  {tag}: " + " ".join(f"{v:.2f}" for v in fa))

print("\n--- 旧 main 里搜 ±2500 量级的 float（编码器计数）---")
hits = []
for off in range(0, len(old300)-4, 4):
    v = struct.unpack_from("<f", old300, off)[0]
    if 2400 < abs(v) < 2700:
        hits.append((off, v))
print(f"  命中 {len(hits)} 处: {[(hex(o), round(v,2)) for o, v in hits[:10]]}")

print("\n--- 新 R6 同范围内搜 ±2500 量级的 float ---")
hits2 = []
for off in range(0, len(slice_new)-4, 4):
    v = struct.unpack_from("<f", slice_new, off)[0]
    if 2400 < abs(v) < 2700:
        hits2.append((off, v))
print(f"  命中 {len(hits2)} 处: {[(hex(o), round(v,2)) for o, v in hits2[:10]]}")
