# -*- coding: utf-8 -*-
"""分析静止稳定性：6 轮之间页内容是否变化，并解码记录与位姿。"""
import pathlib, struct, collections

D = pathlib.Path(r"D:\mydata\workspace\data\reboot_probe\stab")
print("base =", (D/"base.txt").read_text().strip())
for i in range(1, 7):
    print(f"  t{i} =", (D/f"t{i}.time").read_text().strip())

for pg in (132, 133):
    frames = [ (D/f"p{pg}_{i}.bin").read_bytes() for i in range(1, 7) ]
    a = frames[0]
    print(f"\n===== page {pg} =====")
    for i, f in enumerate(frames[1:], start=2):
        d = [k for k in range(4096) if a[k] != f[k]]
        nz = sum(1 for x in f if x)
        print(f"  r1 vs r{i}: 差异 {len(d):>4} 字节   非零字节 {nz}")
    # 解码 0xE24 处 6 条记录
    print("  --- 各轮 (f0,f1) ---")
    for i in range(6):
        o = 0xE24 + 40*i
        vals = []
        for r in range(6):
            f0 = struct.unpack_from("<f", frames[r], o)[0]
            f1 = struct.unpack_from("<f", frames[r], o+8)[0]
            vals.append(f"({f0:.2f},{f1:.2f})")
        same = len(set(vals)) == 1
        print(f"    轴{i+1}: " + "  ".join(vals) + ("   [稳定]" if same else "   <<< 变化"))

print("\n===== 位姿 (page133+0x04) 各轮 =====")
for i in range(1, 7):
    b = (D/f"pose_{i}.bin").read_bytes()
    v = struct.unpack_from("<6f", b, 0)
    print(f"  r{i}: " + "  ".join(f"{x:>10.3f}" for x in v))
