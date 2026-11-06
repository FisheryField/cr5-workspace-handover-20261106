# -*- coding: utf-8 -*-
"""解析 shm_focus32.tar.gz：清单、元数据、采样内容特征。"""
import tarfile, pathlib, collections, struct, re

P = pathlib.Path(r"D:\mydata\codex\b\dobot-evidence-20260922\shm_focus32.tar.gz")
print(f"归档 {P.name}  {P.stat().st_size:,} B")
with tarfile.open(P, "r:gz") as t:
    ms = t.getmembers()
    print(f"成员总数 {len(ms)}")
    files = [m for m in ms if m.isfile()]
    print(f"  文件 {len(files)}  目录 {len(ms)-len(files)}  解压后 {sum(m.size for m in files):,} B")

    # 按前缀聚合
    agg = collections.Counter(); aggb = collections.Counter()
    for m in files:
        parts = m.name.split("/")
        key = "/".join(parts[:-1]) if len(parts) > 1 else "(root)"
        agg[key] += 1; aggb[key] += m.size
    print("\n--- 按目录聚合 ---")
    for k, n in agg.most_common(20):
        print(f"   {n:5d} 个  {aggb[k]:>10,} B   {k}")

    # 小文件（元数据）
    print("\n--- 非 sN_M.bin 的文件 ---")
    for m in files:
        base = m.name.split("/")[-1]
        if not re.fullmatch(r"s\d+_\d+\.bin", base):
            print(f"   {m.size:>8,} B  {m.name}")
            try:
                data = t.extractfile(m).read()
                print("      " + data[:500].decode("utf-8", "replace").replace("\n", "\n      ")[:600])
            except Exception as e:
                print("      读取失败:", e)

    # 采样文件命名规律
    bins = [m.name.split("/")[-1] for m in files if re.fullmatch(r"s\d+_\d+\.bin", m.name.split("/")[-1])]
    pref = collections.Counter(b.split("_")[0] for b in bins)
    print(f"\n--- .bin 采样文件 ---  前缀分布: {dict(pref)}")
    nums = collections.defaultdict(list)
    for b in bins:
        p, n = b[:-4].split("_")
        nums[p].append(int(n))
    for p in nums:
        v = sorted(nums[p]); print(f"   {p}: {len(v)} 个，编号 {v[0]}–{v[-1]}")
    sizes = collections.Counter(m.size for m in files if re.fullmatch(r"s\d+_\d+\.bin", m.name.split("/")[-1]))
    print(f"   文件大小分布: {dict(sizes)}")
