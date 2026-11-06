# -*- coding: utf-8 -*-
import tarfile, pathlib, struct, re

P = pathlib.Path(r"D:\mydata\codex\b\dobot-evidence-20260922\shm_focus32.tar.gz")
with tarfile.open(P, "r:gz") as t:
    def get(n):
        for m in t.getmembers():
            if m.name.endswith("/" + n):
                return t.extractfile(m).read()
        return None
    main = get("main_0.bin"); aux = get("aux_0.bin")
    s1 = get("s1_0.bin")

def dump(name, d, limit=6):
    print(f"\n===== {name} ({len(d):,} B) 非零区段 =====")
    runs, cur = [], None
    for i, v in enumerate(d):
        if v:
            if cur is None: cur = [i, i]
            else: cur[1] = i
        else:
            if cur is not None and i - cur[1] > 16:
                runs.append(tuple(cur)); cur = None
    if cur: runs.append(tuple(cur))
    print(f"  非零区段 {len(runs)} 处，前 {limit}:")
    for a, b in runs[:limit]:
        seg = d[max(0,a-4):b+5]
        print(f"   @0x{a:05X}–0x{b:05X} ({b-a+1} B)")
        print(f"      hex: {seg.hex()}")
        print(f"      u32: {[hex(struct.unpack_from('<I', d, o)[0]) for o in range(a - a%4, min(b+1, a+48), 4) if o+4 <= len(d)]}")
        asc = re.findall(rb"[ -~]{4,}", d[max(0,a-8):b+40])
        if asc: print(f"      串: {[x.decode() for x in asc][:6]}")

dump("main_0", main)
dump("aux_0", aux)
print("\n===== s1_0 完整结构（前 8 条记录，每条 20 B）=====")
for i in range(8):
    o = i * 20
    vals = struct.unpack_from("<5I", s1, o)
    print(f"   [{i}] @0x{o:03X}  " + "  ".join(f"{v:#010x}({v})" for v in vals))
print("\n===== s1 各记录在 6 个段上的差异（第 3 个字段）=====")
for n in ("s1_0.bin","s2_0.bin","s3_0.bin","s4_0.bin","s5_0.bin","s6_0.bin"):
    d = get(n)
    if d is None: continue
    f3 = [struct.unpack_from("<I", d, i*20+8)[0] for i in range(8)]
    print(f"   {n}: 字段3 = {f3}")
