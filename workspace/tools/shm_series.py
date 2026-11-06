# -*- coding: utf-8 -*-
"""解析 s1..s6 时间序列：找出随时间变化的内存字段。"""
import tarfile, pathlib, re, struct, collections

P = pathlib.Path(r"D:\mydata\codex\b\dobot-evidence-20260922\shm_focus32.tar.gz")
series = collections.defaultdict(dict)
times = []
with tarfile.open(P, "r:gz") as t:
    for m in t.getmembers():
        b = m.name.split("/")[-1]
        mm = re.fullmatch(r"(s\d+)_(\d+)\.bin", b)
        if mm:
            series[mm.group(1)][int(mm.group(2))] = t.extractfile(m).read()
        elif b == "times":
            times = t.extractfile(m).read().decode().split("\n")

for s in sorted(series):
    frames = series[s]
    ks = sorted(frames)
    base = frames[ks[0]]
    # 找非零字节偏移
    nz = [i for i, v in enumerate(base) if v != 0]
    print(f"\n### {s}: {len(ks)} 帧 × {len(base)} B；首帧非零字节 {len(nz)} 个，偏移 {nz[:24]}{' …' if len(nz)>24 else ''}")
    # 找"随时间变化"的偏移
    varying = []
    for i in nz:
        vals = {frames[k][i] for k in ks}
        if len(vals) > 1:
            varying.append(i)
    print(f"    随时间变化的字节: {len(varying)} 个 -> {varying[:20]}")
    # 对非零区域按 4 字节解释
    for off in sorted(set(i - i % 4 for i in nz))[:8]:
        words = [struct.unpack_from("<I", frames[k], off)[0] for k in ks]
        iw = [struct.unpack_from("<i", frames[k], off)[0] for k in ks]
        fw = [round(struct.unpack_from("<f", frames[k], off)[0], 4) for k in ks]
        uniq = len(set(words))
        mark = "  <<< 变化" if uniq > 1 else ""
        print(f"    @0x{off:03X}  u32 {words[0]:>10}   u32序列种类 {uniq:>3}  i32首 {iw[0]:>10}  f32首 {fw[0]:>12}{mark}")
        if uniq > 1 and uniq <= 12:
            print(f"          f32 取值: {sorted(set(fw))[:12]}")
print("\n--- times 首末 ---")
print("   ", times[0] if times else "?", " ... ", times[-2] if len(times) > 1 else "")
