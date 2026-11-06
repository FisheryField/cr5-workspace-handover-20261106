#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 .rdk 内每份脚本条目名（UTF-16）与代码块对应，并搜文件链接路径。"""
import io, re

text = io.open(r"D:\mydata\glm-workplace\data\scripts_ref\rdk_extract.txt", encoding="utf-8", errors="replace").read()

# 1) 站点树里的条目名：UTF-16LE 汉字串（含时间戳快照名）
print("== 站点树条目名（UTF-16）==")
names = []
for m in re.finditer(r"(?:[\u4e00-\u9fffA-Za-z0-9_]\x00){4,}", text):
    s = m.group(0).replace("\x00", "")
    if re.search(r"[\u4e00-\u9fff]", s) and len(s) >= 4:
        names.append((m.start(), s))
for pos, s in names:
    print("  at %8d : %s" % (pos, s[:50]))

# 2) coding marker 位置（脚本块起点）
markers = [m.start() for m in re.finditer(r"# -\*- coding: utf-8 -\*-", text)]
# shebang 起点（比 coding marker 更早）
shebangs = [m.start() for m in re.finditer(r"#!/usr/bin/env python3", text)]

print()
print("== 脚本块起点（shebang/coding）==")
starts = sorted(set(shebangs + markers))
print("shebangs:", shebangs)
print("coding  :", markers)

# 3) 搜文件链接（磁盘路径引用）
print()
print("== 磁盘路径引用 ==")
for m in re.finditer(r"[A-Za-z]:\\[^\x00\n\"<>]{4,120}\.py", text):
    print("  at %8d : %s" % (m.start(), m.group(0)))

# 4) 每份脚本块 -> 最近的前置条目名
print()
print("== 脚本块 ↔ 条目名对应 ==")
ends = []
for st in starts:
    em = re.search(r"root\.mainloop\(\)", text[st:])
    ends.append(st + (em.end() if em else 0))
for i, st in enumerate(starts):
    prior = [p for p, s in names if p < st]
    nm = names[prior.index(max(prior))][1] if prior else "?"
    seg = text[st:ends[i] if ends[i] > st else st + 200]
    kind = "仿真" if "RUNMODE_SIMULATE" in seg or "仿真" in seg[:2000] else "?"
    retreat = "有退让" if "_retreat_orientation_records" in seg else "无退让"
    print("  块%02d chars=%6d 条目=%-28s %s %s" % (i, ends[i] - st, nm[:28], kind, retreat))
