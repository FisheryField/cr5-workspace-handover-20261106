# -*- coding: utf-8 -*-
"""紧凑分析 shm_focus32.tar.gz：结构、元数据、内容特征。"""
import tarfile, pathlib, collections, re, struct

P = pathlib.Path(r"D:\mydata\codex\b\dobot-evidence-20260922\shm_focus32.tar.gz")
out = []
def p(s=""): out.append(str(s))

with tarfile.open(P, "r:gz") as t:
    ms = [m for m in t.getmembers() if m.isfile()]
    p(f"归档 {P.stat().st_size:,} B   成员 {len(ms)}   解压后合计 {sum(m.size for m in ms):,} B")
    grp = collections.defaultdict(lambda: [0, 0])
    for m in ms:
        b = m.name.split("/")[-1]
        if re.fullmatch(r"main_\d+\.bin", b):   k = "main_*"
        elif re.fullmatch(r"aux_\d+\.bin", b):  k = "aux_*"
        elif re.fullmatch(r"s\d+_\d+\.bin", b): k = "sN_M（时间序列采样）"
        else:                                     k = "(元数据) " + b
        grp[k][0] += 1; grp[k][1] += m.size
    p("\n--- 分组 ---")
    for k, (n, b) in sorted(grp.items()):
        p(f"   {k:26} {n:5d} 个  {b:>12,} B")

    def show(name, limit=1400):
        for m in ms:
            if m.name.split("/")[-1] == name:
                d = t.extractfile(m).read()
                p(f"\n--- {name} ({len(d):,} B) ---")
                p(d[:limit].decode("utf-8", "replace"))
                return
    for n in ("maps", "start", "pid", "events.log", "ps"):
        show(n)

    # times 抽样
    for m in ms:
        if m.name.endswith("/times"):
            txt = t.extractfile(m).read().decode("utf-8", "replace").splitlines()
            p(f"\n--- times ({len(txt)} 行) 前 3 / 后 3 ---")
            p("   " + " | ".join(txt[:3])); p("   " + " | ".join(txt[-3:]))

    # 内容特征
    p("\n--- 内容特征（各取前若干文件）---")
    def zero_frac(d):
        return d.count(0) / max(1, len(d))
    for k, pat in (("main_*", r"main_\d+\.bin"), ("aux_*", r"aux_\d+\.bin"), ("sN_M", r"s\d+_\d+\.bin")):
        sel = [m for m in ms if re.fullmatch(pat, m.name.split("/")[-1])][:6]
        for m in sel:
            d = t.extractfile(m).read()
            nz = len(d) - d.count(0)
            asc = len(re.findall(rb"[ -~]{6,}", d))
            p(f"   {m.name.split('/')[-1]:16} {len(d):>8,} B  非零字节 {nz:>8,} ({nz*100//max(1,len(d))}%)  可读串 {asc}")
print("\n".join(out))
