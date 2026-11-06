# -*- coding: utf-8 -*-
import pathlib, re, collections, struct, sys

D = pathlib.Path(r"D:\mydata\workspace\data\captures\zero_shm_20260923_112646\zero_shm_20260923_112646")
rounds = [l.split() for l in (D/"rounds.txt").read_text().splitlines() if l.strip()]
tmap = {int(a): float(b) for a, b in rounds}
T0 = float(rounds[0][1]); CAL = T0 + 8.0

# ---- (a) 持久差异：base vs cur ----
print("=== (a) 基线 vs 最后一轮（持久变化）===")
for f in sorted((D/"base").glob("R*.bin")):
    idx = f.stem[1:]
    c = D/"cur"/f.name
    if not c.exists(): continue
    a = f.read_bytes(); b = c.read_bytes()
    n = min(len(a), len(b))
    diff = [i for i in range(n) if a[i] != b[i]]
    if not diff:
        print(f"  R{idx}: 无差异")
        continue
    pages = collections.Counter(i//4096 for i in diff)
    print(f"  R{idx}: {len(diff)} 字节不同，涉 {len(pages)} 页 -> " +
          ", ".join(f"p{p}({c2})" for p, c2 in pages.most_common(6)))
    # 打印每页前若干差异的"值前后"
    for p, _ in pages.most_common(3):
        offs = [i for i in diff if i//4096 == p][:8]
        seg = f"  p{p} offs={offs} before={[a[o] for o in offs]} after={[b[o] for o in offs]}"
        print(seg)
        # 若偏移对齐 4 字节，给出 float32 解释
        for o in offs[:4]:
            o4 = o - o % 4
            fa = struct.unpack_from("<f", a, o4)[0]; fb = struct.unpack_from("<f", b, o4)[0]
            ia = struct.unpack_from("<i", a, o4)[0]; ib = struct.unpack_from("<i", b, o4)[0]
            if abs(fa) > 1e-6 or abs(fb) > 1e-6:
                print(f"      @0x{o4:X}  f32 {fa:.6g} -> {fb:.6g}   i32 {ia} -> {ib}")

# ---- (b) 逐轮变化量的时间序列（标定前 5 轮 ~ 后 12 轮）----
print("\n=== (b) 标定(轮9-11)前后，各页每轮变化字节数 ===")
data = collections.defaultdict(dict)   # (reg,page) -> {round: bytes}
cur = None
for l in (D/"changes.txt").read_text(errors="replace").splitlines():
    m = re.match(r"round=(\d+) t=([\d.]+) region=(\d+) name=(\S+)", l)
    if m:
        cur = (int(m.group(1)), float(m.group(2)), int(m.group(3))); continue
    m = re.match(r"\s+pages:\s+(.*)", l)
    if m and cur:
        for tok in m.group(1).split():
            if ":" in tok:
                pg, cnt = tok.split(":")
                data[(cur[2], int(pg))][cur[0]] = int(cnt)
for key in sorted(data):
    ser = data[key]
    if len(ser) < 3: continue
    rmin, rmax = min(ser), max(ser)
    if rmax < 3: continue
    rows = []
    for r in range(1, min(rmax, 24)+1):
        rows.append(f"{ser.get(r,0):>4}")
    print(f"  region={key[0]} page={key[1]:<5} 轮1..{min(rmax,24)}: " + "".join(rows))
print("\n  （标定在轮 9–11）")
