# -*- coding: utf-8 -*-
"""分析标定采集：把"只在该时刻才变化的页"挑出来。"""
import pathlib, re, collections, sys

D = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else r"D:\mydata\workspace\data\captures\zero_shm_20260923_112646\zero_shm_20260923_112646")
ch = (D / "changes.txt").read_text(errors="replace").splitlines()
rounds = [l.split() for l in (D / "rounds.txt").read_text().splitlines() if l.strip()]
tmap = {int(a): float(b) for a, b in rounds}
print(f"轮数 {len(rounds)}  t 范围 {rounds[0][1]} → {rounds[-1][1]}")

# 标定发生时间：窗口内第 8 秒 → 换算成 uptime
t0 = float(rounds[0][1])
CAL_T = t0 + 8.0          # 11:26:52.543 - 11:26:44 ≈ 8.5s
print(f"标定时刻 ≈ uptime {CAL_T:.1f}（轮次 {[k for k,v in tmap.items() if abs(v-CAL_T)<1.2]}）")

# 解析：每区域每页的变化时间线
page_rounds = collections.defaultdict(list)
page_bytes  = collections.defaultdict(list)
cur = None
for l in ch:
    m = re.match(r"round=(\d+) t=([\d.]+) region=(\d+) name=(\S+) diffs=(\d+) pages=(\d+)", l)
    if m:
        cur = (int(m.group(1)), float(m.group(2)), int(m.group(3)), m.group(4), int(m.group(5)))
        continue
    m = re.match(r"\s+pages:\s+(.*)", l)
    if m and cur:
        rnd, t, reg, name, diffs = cur
        for tok in m.group(1).split():
            if ":" in tok:
                pg, cnt = tok.split(":")
                page_rounds[(reg, int(pg))].append(rnd)
                page_bytes[(reg, int(pg))].append(int(cnt))

print(f"\n共 {len(page_rounds)} 个 (区域,页) 组合出现过变化")

# 分类
before, calib, late = [], [], []
for key, rlist in sorted(page_rounds.items()):
    first = min(rlist)
    ft = tmap.get(first, 0)
    rec = (key, first, ft, len(rlist), max(page_bytes[key]))
    if ft < CAL_T - 1.5: before.append(rec)
    elif ft <= CAL_T + 6: calib.append(rec)
    else: late.append(rec)

def show(title, lst, limit=25):
    print(f"\n===== {title}（{len(lst)} 个）=====")
    for (reg, pg), first, ft, n, mx in sorted(lst, key=lambda x: x[3], reverse=True)[:limit]:
        print(f"  region={reg} page={pg:<6} 首变轮次={first:<4} t={ft:<9.2f} 变化轮数={n:<4} 单轮最大字节={mx}")

show("标定【前】就在变（噪声页）", before)
show("标定【当时】开始变（★候选）", calib)
show("标定之后才开始变", late)
