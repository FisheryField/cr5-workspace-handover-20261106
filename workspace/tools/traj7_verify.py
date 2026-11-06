#!/usr/bin/env python3
"""对比 连续轨迹7 基准/优化两版运行日志：
1. 预检段判定行（分支失败/通过/粗筛日志）逐步对照，必须完全一致；
2. 执行段（正式仿真运动）逐点对照：方法、J6目标必须完全一致。
"""
import re
import sys

BASE = "_traj7_baseline.log"
OPT = "_traj7_optimized.log"
TIME = re.compile(r"^\[\s*\d+\.\ds\]\s*")
NOISE = ("PySide2", "[runner]", "函数体已注入", "robomath/robolink 符号已补齐", "python :", "Traceback", "RunMode=")

def load(path):
    raw_bytes = open(path, "rb").read()
    enc = "utf-16" if raw_bytes[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    lines = []
    for raw in raw_bytes.decode(enc, errors="replace").splitlines():
        line = TIME.sub("", raw).strip()
        if not line or any(s in line for s in NOISE):
            continue
        if "各阶段耗时统计" in line:  # 统计段起，全部丢弃
            break
        lines.append(line)
    return lines

base, opt = load(BASE), load(OPT)
cut_b = next(i for i, l in enumerate(base) if "正式仿真运动" in l)
cut_o = next(i for i, l in enumerate(opt) if "正式仿真运动" in l)
head_b, head_o = base[:cut_b], opt[:cut_o]

def is_judgment(line):
    return ("候选分支未通过" in line or "预检通过" in line or "MoveL原生路径检查未通过" in line
            or "没有找到整段可行" in line or "MoveJ快速筛选" in line)

jb = [l for l in head_b if is_judgment(l)]
jo = [l for l in head_o if is_judgment(l)]
print("== 预检段判定行对照：基准 %d 条 / 优化 %d 条 ==" % (len(jb), len(jo)))
ok = len(jb) == len(jo)
if ok:
    for i, (a, b) in enumerate(zip(jb, jo), 1):
        if a != b:
            ok = False
            print("  DIFF #%02d" % i)
            print("    B: %s" % a[:120])
            print("    O: %s" % b[:120])
if ok:
    print("  全部 %d 条判定行逐步一致 ✓" % len(jb))

def exec_lines(lines):
    out = []
    for l in lines:
        m = re.match(r"(P\d+)[（(]?[^ ）]*[）)]? (开始|->) (MoveJ|MoveL)[^，。]*", l)
        if m:
            j6 = l.split("J6目标=")[-1] if "J6目标=" in l else ""
            out.append((m.group(1), m.group(2), m.group(3), j6))
    return out

eb, eo = exec_lines(base), exec_lines(opt)
print("\n== 执行段逐点对照（%d vs %d 条）==" % (len(eb), len(eo)))
mismatch = 0
for i, (a, b) in enumerate(zip(eb, eo), 1):
    if a != b:
        mismatch += 1
        print("  DIFF #%d\n    B: %s\n    O: %s" % (i, a, b))
if len(eb) != len(eo):
    mismatch += 1
    print("  行数不同：%d vs %d" % (len(eb), len(eo)))
print("  逐点（点号/阶段/方法/J6目标）%s（%d/%d 一致）"
      % ("完全一致 ✓" if mismatch == 0 else "存在差异 ✗", len(eb) - min(mismatch, len(eb)), len(eb)))
sys.exit(0 if ok and mismatch == 0 else 1)
