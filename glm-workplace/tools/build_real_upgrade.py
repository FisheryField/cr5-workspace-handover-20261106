#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 构建 TCP真实运动 升级版：磁盘版为底 + 仿真副本的连续运动逻辑移植。
# 改动清单：
#   1. 缓存三件套 + TCP->法兰换算（提速，语义不变）
#   2. _validated_records 扩展：spin360 自转点（±360、六维与前点相同）
#   3. _retreat_orientation_records 姿态退让展开 + _execute_checked_real 接入
#   4. _plan_continuous_trajectory 换成仿真版（自转360/不可达预检/require_linear/缓存）
#   5. _linear_path_endpoint/_obstacle_joint_target 换缓存版(+uncached)
#   6. _checked_j6_rewinds 缓存版；_enable_obstacle_checks 清缓存+磨砂圆柱
#   7. _check_single_joint_path/_verify_obstacle_plan/_trajectory_start_candidates 对齐
#   8. GUI：自转360复选框、列表标记、加点逻辑、启动日志、文件头
import io, sys, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)

BASE = r"D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂TCP真实运动.py"
SIM = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
OUT = r"D:\mydata\glm-workplace\sim_scripts\TCP真实运动_升级版.py"

base_lines = io.open(BASE, encoding="utf-8", errors="replace").read().splitlines()
sim_src = io.open(SIM, encoding="utf-8", errors="replace").read()
sim_lines = sim_src.splitlines()

def sim_func(name):
    tree = ast.parse(sim_src)
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return "\n".join(l.rstrip() for l in sim_lines[n.lineno - 1:n.end_lineno])
    raise KeyError(name)

def base_spans():
    tree = ast.parse("\n".join(base_lines))
    return {n.name: (n.lineno, n.end_lineno) for n in tree.body if isinstance(n, ast.FunctionDef)}

spans = base_spans()

# ---------- 函数级替换（自底向上拼接） ----------
repl = []  # (start_line_1based, end_line_1based, new_text)
repl.append((spans["_validated_records"][0], spans["_validated_records"][1], '''def _validated_records(data):
    if not isinstance(data, list) or not data:
        raise ValueError('轨迹必须是非空点列表。')
    result = []
    for i, rec in enumerate(data, 1):
        kind = str(rec.get('type', '')).upper()
        if kind == 'JNT':
            kind = 'JOINT'
        values = [float(v) for v in rec.get('values', [])]
        if kind not in ('TCP', 'JOINT') or len(values) != 6 or not all(math.isfinite(v) for v in values):
            raise ValueError(f'P{i}：类型或六维数值无效。')
        special = bool(rec.get('singular', False)) and kind == 'TCP'
        spin = special and bool(rec.get('spin360', False))
        raw_delta = int(rec.get('j6_delta', 360 if spin else 180)) if special else 0
        if special and (not result or result[-1]['type'] != 'TCP' or result[-1]['singular']):
            raise ValueError(f'P{i}：特异点前序或转向无效。')
        if special:
            if spin:
                if raw_delta not in (-360, 360):
                    raise ValueError(f'P{i}：J6自转方向必须为+360或-360。')
                if max(abs(a - b) for a, b in zip(values, result[-1]['values'])) > 1e-3:
                    raise ValueError(f'P{i}：J6自转360°特异点的六维数值必须与前一个TCP点完全相同。')
            elif raw_delta not in (-180, 180):
                raise ValueError(f'P{i}：J6方向必须为+180或-180。')
        delta = (360 if spin else 180) * (1 if raw_delta >= 0 else -1) if special else 0
        result.append(dict(type=kind, values=values, singular=special, spin360=spin, j6_delta=delta))
    return result'''))

repl.append((spans["add_and_check_trajectory_point"][0], spans["add_and_check_trajectory_point"][1], '''def add_and_check_trajectory_point():
    values = _parse_six_from_entries(traj_entries, traj_type.get())
    if values is None:
        return
    kind = traj_type.get()
    is_singular = kind == 'TCP' and bool(singular_var.get())
    spin = is_singular and bool(spin_var.get())
    sign = 1 if int(j6_direction_var.get()) >= 0 else -1
    rec = dict(type=kind, values=values, singular=is_singular, spin360=spin,
               j6_delta=sign * (360 if spin else 180))
    try:
        records = _validated_records(trajectory_records + [rec])
    except ValueError as exc:
        log('点未加入：' + str(exc))
        return
    trajectory_records[:] = records
    refresh_record_list()
    if spin:
        log('P%d [TCP-J6自转360°]：已加入；执行时 J1~J5 不变，J6 %+d°。' % (len(records), sign * 360))
    else:
        log('点已加入；完整避障预检将在执行前进行。关节圈数按输入保留。')'''))

for name in ("_plan_continuous_trajectory", "_checked_j6_rewinds",
             "_enable_obstacle_checks", "_check_single_joint_path",
             "_verify_obstacle_plan", "_trajectory_start_candidates"):
    repl.append((spans[name][0], spans[name][1], sim_func(name)))

repl.append((spans["_linear_path_endpoint"][0], spans["_linear_path_endpoint"][1],
             sim_func("_linear_path_endpoint") + "\n\n\n" + sim_func("_linear_path_endpoint_uncached")))
repl.append((spans["_obstacle_joint_target"][0], spans["_obstacle_joint_target"][1],
             sim_func("_obstacle_joint_target") + "\n\n\n" + sim_func("_obstacle_joint_target_uncached")))
# 退让展开：插到 _prepare_real_plan 之前
pp = spans["_prepare_real_plan"]
repl.append((pp[0], pp[0] - 1, sim_func("_retreat_orientation_records") + "\n\n\n"))
# 缓存三件套 + TCP->法兰换算：插到 _real_running = False 之后
anchor = None
for idx, l in enumerate(base_lines):
    if l.strip() == "_real_running = False":
        anchor = idx + 1
        break
assert anchor, "anchor _real_running not found"
blockA = "\n\n".join([
    "# 预检缓存（与TCP仿真副本同款）：生命周期=单次预检规划，_enable_obstacle_checks 每次进入预检时清空。",
    "_plan_cache = {}",
    sim_func("_cache_key_joints"), sim_func("_cache_key_pose"), sim_func("_movej_test_cached"),
    sim_func("_tcp_target_to_flange"), sim_func("_flange_target_description")])
repl.append((anchor, anchor, blockA + "\n"))

repl.sort(key=lambda r: r[0])
out = []
prev_end = 0
for start, end, text in repl:
    out.extend(base_lines[prev_end:start - 1])
    out.extend(text.splitlines())
    prev_end = end
out.extend(base_lines[prev_end:])
src = "\n".join(out) + "\n"

# ---------- 文本级补丁 ----------
patches = [
 ("- 连续轨迹：坐标列表 -> 逐点 IK 检测 -> MoveJ+MoveL 序列",
  "- 连续轨迹：与TCP仿真同款（姿态退让、J6特异点±180°/自转360°、避障规划+缓存）\n2026-10-09：连续运动逻辑对齐 机械臂TCP仿真_副本.py"),
 ("singular_var = None\nj6_direction_var = None",
  "singular_var = None\nj6_direction_var = None\nspin_var = None"),
 ('            mark = " [J6特异点 %s180°]" % ("+" if rec.get("j6_delta", 180) >= 0 else "-") if rec.get("singular", False) else ""',
  '            if rec.get("spin360", False):\n                mark = " [J6自转360° %s]" % ("+" if rec.get("j6_delta", 360) >= 0 else "-")\n            elif rec.get("singular", False):\n                mark = " [J6特异点 %s180°]" % ("+" if rec.get("j6_delta", 180) >= 0 else "-")\n            else:\n                mark = ""'),
 ("        records = _validated_records(data)\n        deviation = float(real_deviation_var.get())",
  "        records = _validated_records(data)\n        if single_method is None and len(records) > 1:\n            expanded = _retreat_orientation_records(records)\n            log('连续轨迹：%d个录入点展开为%d个执行点（含姿态退让）。' % (len(records), len(expanded)))\n            records = expanded\n        deviation = float(real_deviation_var.get())"),
 ('text="末端特异点（跳过IK，仅J6转180°）",',
  'text="末端特异点（跳过IK，仅J6转动）",'),
 ('tk.Radiobutton(singular_frame, text="-180°", variable=j6_direction_var, value=-180).pack(side=tk.LEFT, padx=3)',
  'tk.Radiobutton(singular_frame, text="-180°", variable=j6_direction_var, value=-180).pack(side=tk.LEFT, padx=3)\nspin_var = tk.BooleanVar(value=False)\ntk.Checkbutton(singular_frame, text="J6自转360°（第二类，六维与前点相同）", variable=spin_var).pack(side=tk.LEFT, padx=3)'),
 ('log("连续运动：避障优先、J6自动±180°，整段预检通过后执行；驱动报断连须连续反馈确认到位，其余异常停止后续命令。")',
  'log("连续运动：避障优先、姿态退让、J6特异点±180°/自转360°，整段预检通过后执行；驱动报断连须连续反馈确认到位，其余异常停止后续命令。")'),
]
for old, new in patches:
    n = src.count(old)
    assert n == 1, "补丁锚点命中 %d 次（应为1）：%r" % (n, old[:50])
    src = src.replace(old, new)

io.open(OUT, "w", encoding="utf-8", newline="\n").write(src)

# ---------- 校验 ----------
tree = ast.parse(src)
funcs = {n.name: (n.lineno, n.end_lineno) for n in tree.body if isinstance(n, ast.FunctionDef)}
lines = src.splitlines()
print("构建完成:", OUT, "共", len(lines), "行；语法 OK；函数数:", len(funcs))

must_match = ["_plan_continuous_trajectory", "_checked_j6_rewinds", "_linear_path_endpoint",
              "_linear_path_endpoint_uncached", "_obstacle_joint_target", "_obstacle_joint_target_uncached",
              "_enable_obstacle_checks", "_check_single_joint_path", "_verify_obstacle_plan",
              "_trajectory_start_candidates", "_retreat_orientation_records",
              "_cache_key_joints", "_cache_key_pose", "_movej_test_cached",
              "_tcp_target_to_flange", "_flange_target_description"]
bad = []
for name in must_match:
    mine = "\n".join(l.rstrip() for l in lines[funcs[name][0] - 1:funcs[name][1]])
    if mine != sim_func(name):
        bad.append(name)
print("与仿真副本逐字一致的移植函数: %d/%d" % (len(must_match) - len(bad), len(must_match)))
if bad:
    print("!! 不一致:", bad)
print("spin360 出现次数:", src.count("spin360"), " _retreat 调用:", src.count("_retreat_orientation_records(records)"))
assert "_plan_cache = {}" in src, "_plan_cache 定义缺失"
assert src.count("_plan_cache") >= 10, "_plan_cache 引用异常"
