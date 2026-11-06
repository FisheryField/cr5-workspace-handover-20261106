# -*- coding: utf-8 -*-
"""重新检查旧采集的 main_*.bin 是否随时间变化（之前漏检了）。"""
import tarfile, pathlib, re, struct

P = pathlib.Path(r"D:\mydata\codex\b\dobot-evidence-20260922\shm_focus32.tar.gz")
frames = {}
with tarfile.open(P, "r:gz") as t:
    for m in t.getmembers():
        b = m.name.split("/")[-1]
        mm = re.fullmatch(r"main_(\d+)\.bin", b)
        if mm:
            frames[int(mm.group(1))] = t.extractfile(m).read()
ks = sorted(frames)
print(f"main 帧数 {len(ks)}  大小 {len(frames[ks[0]]):,} B")

# 关注地址：新采集里零点数据在 0x73A84E24；main 基址 0x73A40000 -> 偏移 0x44E24
OFF = 0x44E24
print(f"\n=== 偏移 0x{OFF:X}（= 绝对 0x73A84E24）在各帧的值 ===")
vals = []
for k in ks:
    v = struct.unpack_from("<f", frames[k], OFF)[0]
    vals.append(v)
uniq = sorted(set(round(v,3) for v in vals))
print(f"  出现 {len(uniq)} 种取值: {uniq[:12]}")
# 找出变化点
prev = None
for k in ks:
    v = struct.unpack_from("<f", frames[k], OFF)[0]
    if prev is not None and abs(v-prev) > 1e-6:
        print(f"  帧 {k-1} -> {k}: {prev} -> {v}")
    prev = v

# 整块差异：帧0 vs 帧100/200/300
print("\n=== 帧0 与其他帧的差异统计 ===")
a = frames[ks[0]]
for k in (40, 80, 100, 120, 150, 200, 250, 300):
    if k not in frames: continue
    b = frames[k]
    d = [i for i in range(0, min(len(a), len(b))) if a[i] != b[i]]
    pages = sorted(set(i//4096 for i in d))
    print(f"  帧0 vs 帧{k}: {len(d)} 字节不同，页 {pages[:14]}")
    if 0x44 in pages or any(p*4096 <= OFF < (p+1)*4096 for p in pages):
        offs = [i for i in d if abs(i-OFF) < 0x100][:6]
        print(f"      靠近 0x{OFF:X} 的差异偏移: {[hex(o) for o in offs]}")
        for o in offs:
            fa = struct.unpack_from("<f", a, o - o%4)[0]; fb = struct.unpack_from("<f", b, o - o%4)[0]
            print(f"        @0x{o-o%4:X}  {fa:.4f} -> {fb:.4f}")
