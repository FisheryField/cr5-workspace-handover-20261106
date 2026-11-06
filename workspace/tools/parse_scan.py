# -*- coding: utf-8 -*-
import re, pathlib, collections
txt = pathlib.Path(r"D:\mydata\workspace\_scan_raw.txt").read_text(errors="replace")
res = collections.defaultdict(dict)   # slave -> index -> value or FAIL
for line in txt.splitlines():
    line = line.strip()
    if not line.startswith("READ|"): continue
    parts = line.split("|")
    if len(parts) < 4: continue
    slave, idx, payload = parts[1], parts[2], "|".join(parts[3:]).strip()
    m = re.search(r"0x[0-9A-Fa-f]{4}:[0-9]+s*=s*(.+)$", payload)
    val = m.group(1).strip() if m else payload
    res[slave][idx] = "FAIL" if "<FAIL>" in payload else val

idx_order = [k for k in res["8"] if k.startswith("0x") and len(k) == 6]
print(f"{'索引':<10} {'slave7 (3.1.5.0)':<20} {'slave8 (3.2.D.8)':<20} 差异")
diff = 0
for i in idx_order:
    a = res["7"].get(i, "?"); b = res["8"].get(i, "?")
    mark = ""
    if (a == "FAIL") != (b == "FAIL"):
        mark = "  <<<<< 存在性不同"; diff += 1
    print(f"{i:<10} {a:<20} {b:<20}{mark}")
print(f"\n存在性不同的索引: {diff}")
print("\n存在的（两侧一致且非 FAIL）:", " ".join(i for i in idx_order if res["7"].get(i) != "FAIL"))
print("\n子索引扫描:")
for k in res["8"]:
    if ":" in k: print("  ", k, "->", res["8"][k][:200])
for k in res["7"]:
    if ":" in k: print("  ", k, "->", res["7"][k][:200])
