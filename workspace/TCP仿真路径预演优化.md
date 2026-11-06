# 机械臂TCP仿真.py 路径预演提速 — 解读、实测与已实施的优化

> 2026-09-25。对象：`机械臂TCP仿真.py`（补丁前 58,569 B / ~1230 行）。
> 结论先行：**优化已实施并验证**——同一条 `连续轨迹7.json`（11 原始点 → 17 执行点）
> 整段预检 **285.4 s → 96.1 s（约 1/3）**，总耗时 305.8 s → 116.2 s，
> **最终执行计划与执行轨迹 17/17 点逐点一致**（方法 + 每点 J6 目标全部相同）。
> 碰撞安全判定粒度未放宽：MoveL 逐段仍是 1 mm 全粒度，整段终检仍 1 mm + 碰撞 ON。

---

## 1. 脚本结构（连续轨迹执行链）

两个选项卡。连续轨迹执行链（本次优化对象）：

```
连续轨迹.json 导入
  → 加点时：add_and_check_trajectory_point（逐点 IK + 段内 21 点连续 IK 采样）
  → 执行按钮：execute_recorded_trajectory
      → _retreat_orientation_records     # y=-775 加工位变姿态 → 自动展开 y=-750 退让/换向点(require_linear)
      → _plan_continuous_trajectory      # ★ 整段预检（热点，93% 耗时）
      → Trace On → 逐点 MoveL/MoveJ      # 每步对照预检关节，偏差>0.1°即停
```

`_plan_continuous_trajectory` 的搜索结构（三层嵌套全遍历）：

```
for allow_rewind in (False, True):                    # 整圈回绕兜底，两轮
  for seed in _trajectory_start_candidates(...):       # 首TCP的 SolveIK_All 全解 × J6±360，按避障姿态排序
    for directions in product(±180°, ...):             # 每个特异点两个方向，2^S 组合
      逐点：_linear_path_endpoint（MoveL）
            失败 → _obstacle_joint_target（MoveJ 兜底选解）+ _check_movej_tcp_trajectory(100) + MoveJ_Test(0.25°)
      特异点：J6 ±180° + FK 核对（不走 IK）
      任何点失败 → 换分支从头重规划（failed_prefixes 仅按 seed+方向前缀剪枝）
  全部通过 → _verify_obstacle_plan（整段 InstructionListJoints 1mm + 碰撞ON，权威终检）
```

`_linear_path_endpoint` = `MoveL_Test(1mm)`（碰撞已开）+ 建临时程序 `InstructionListJoints(1mm, 碰撞ON)`
——后一次调用**只为读实际终点关节**（本机 MoveL_Test 成功后 `Joints()` 可能全零，注释写明）。

## 2. 瓶颈实测（先实测后开方）

单 API 计时（`tools/rdk_timing_probe.py`，本机 RoboDK + CR5 工作站）：

| 调用 | 条件 | 耗时 |
|---|---|---|
| SolveFK / Joints / JointPoses / PoseFrame+PoseTool | — | 0.12–0.24 ms（**不是瓶颈**） |
| MoveL_Test 50 mm | 步长 10 mm | 108 ms |
| MoveL_Test 50 mm | 步长 1 mm | **1090 ms（≈22 ms/mm）** |
| InstructionListJoints（MoveJ+MoveL 50mm @1mm，212 行） | 碰撞 OFF | 9–13 ms |
| 同上 | 碰撞 ON | **2174 ms（≈10 ms/行，差 ~170 倍）** |
| MoveJ_Test 20° | 0.25°–1° | 118–124 ms |

整段实测（`tools/traj7_baseline_run.py`，AST 原样提取脚本全部函数、无头注入、与 GUI 执行按钮同路径）：

| 阶段 | 次数 | 耗时 | 占比 |
|---|---|---|---|
| `_linear_path_endpoint` | 67 | **189.8 s** | 62% |
| `_verify_obstacle_plan`（整段终检） | 1 | 35.4 s | 12% |
| `_obstacle_joint_target` | 14 | 24.5 s | 8% |
| 其余（候选/FK 采样等） | — | ~35 s | |
| **预检合计** | | **285.4 s** | **93%** |
| 动画播放（SIM_SPEED=50） | 17 点 | ~20 s | 7% |

日志直接可见的浪费：P1→P2 那段 ~1 m 长直线，`_linear_path_endpoint` 以 18.1–18.4 s/次
的价格被原样重算 ≥5 次（第 1/10/19/25/34 次调用）；「MoveJ快速筛选：21个候选…」同一目标的兜底搜索日志重复 4–5 次。

## 3. 三个判决性发现

1. **同一路径碰撞查两遍**：`_linear_path_endpoint` 里 `InstructionListJoints(collision_check=ON)`
   只为提取终点关节，碰撞开关不影响终点值。碰撞判定由同路径、同 1 mm 粒度的 `MoveL_Test`
   与整段 `_verify_obstacle_plan` 负责——这里关掉是纯提速，不改任何判定。
2. **分支重试全量重算**：`_linear_path_endpoint` / `_obstacle_joint_target` /
   `_checked_j6_rewinds` / `_movej_test` 都是纯函数（输出只依赖输入关节+目标+参数），
   2^S × 种子的全遍历反复重算相同前缀，却没有任何缓存。
3. **粗筛子集论证**：`MoveL_Test` 的粗(10 mm)/细(1 mm)采样点都从 t=0 等距生成，
   粗点集 ⊂ 细点集 ⇒ **粗筛失败 ⇒ 细查必失败**，可安全短路；通过段再跑 1 mm 细查，判定逐位一致。

## 4. 已实施的补丁（11 个 hunk，全部在预检函数内部）

| # | 改动 | 性质 |
|---|---|---|
| 1 | 模块顶部新增 `_plan_cache` + `_cache_key_joints/_cache_key_pose` + `_movej_test_cached` | 新增基础设施 |
| 2 | `_linear_path_endpoint` 拆为缓存壳 + `_linear_path_endpoint_uncached`；内部先 10 mm 粗筛再 1 mm 细查 | 判定不变（发现 3） |
| 3 | 终点提取 `InstructionListJoints` 改 `COLLISION_OFF` | 判定不变（发现 1） |
| 4 | `_obstacle_joint_target` 拆缓存壳 + `_uncached`（ValueError 也缓存） | 判定不变 |
| 5 | 兜底精查 `MoveJ_Test(.25°)` 走缓存 | 判定不变 |
| 6 | `_checked_j6_rewinds` 生成器 → 缓存列表（两个调用点都是 for 迭代，兼容） | 判定不变 |
| 7–9 | 单点/起始姿态/规划循环内的 `MoveJ_Test(1°)` 走缓存 | 判定不变 |
| 10 | `_enable_obstacle_checks()` 入口清空缓存 | **缓存生命周期 = 单次预检**；障碍物改动下次预检即时生效 |
| 11 | 启动日志注明「预检带结果缓存与MoveL粗筛」 | 提示 |

刻意**不做**的事：不动执行逻辑、特异点/退让语义、MoveJ 兜底顺序、日志判据（>0.1° 停机检查）；
调用方对返回列表只读或拷贝（已逐点核对 `end[:]`/`plan.append(dict(joints=end[:]))`），缓存共享安全；
缓存命中时不复现"仿真关节停在终点"的副作用，但已核对所有消费方都只依赖局部关节变量。

## 5. 等价性验证（实测证据链）

1. **执行轨迹逐点一致**：基准 vs 优化，P1–P17 每点的方法（MoveJ/MoveL）与 J6 目标
   全部相同（`tools/traj7_verify.py`，17/17 ✓）；两版最终计划同为「首个TCP J6=−106.380°」，
   权威终检（1 mm + 碰撞 ON）两版都通过。
2. **分支失败序列一致**：优化版 = 原版复跑 1，逐项相同（P11, P11, P8, P11, P8, P15）。
3. **「日志行数差异」的解释（重要）**：预检中间日志行数在**原代码自身**的多次运行间就漂移
   （原版三次运行：7 / 6 / 15 次分支失败，首跑多出的 P3 是死路分支）。
   原因：分支枚举顺序依赖种子排序，而 `_obstacle_posture_key` 的避障姿态排序依赖
   RoboDK 内部返回顺序；规划是**全遍历**，中间探索可漂移，**最终计划不变**（三次原版复跑收敛到同一计划）。
   逆向验证：`tools/traj7_make_original.py` 从补丁版逐块还原出原版
   （58,569 B，与存档记录的原始大小逐字节吻合），连跑两遍取得上述对照。
4. **单点选项卡冒烟**：`_obstacle_joint_target` → `_check_single_joint_path` 链路通过
   （`tools/traj7_singlepoint_smoke.py`）。
5. 全文件扫描：裸 `robot.MoveJ_Test` 仅剩缓存包装内部 1 处；碰撞开关只动了终点提取一处
   （`_verify_obstacle_plan` 仍 COLLISION_ON）。

已知可接受差异：缓存命中后「MoveJ快速筛选…」日志只打印一次（原先同目标重复打印 4–5 次本就是重复搜索的副产物）。

## 6. 成绩单与剩余空间

| | 补丁前 | 补丁后 |
|---|---|---|
| 整段预检 | 285.4 s | **96.1 s** |
| 其中 `_linear_path_endpoint` | 67 次调用 189.8 s | 65 次调用（实际计算 34 次）**29.4 s** |
| 其中 `_obstacle_joint_target` | 14 次 24.5 s | 13 次（实际计算 7 次）**11.0 s** |
| 整段终检 `_verify_obstacle_plan` | 35.4 s | 36.3 s（未动，权威层） |
| **总耗时（含动画）** | **305.8 s** | **116.2 s** |

剩余大头：① 整段终检 ~36 s（1 mm + 碰撞 ON，是安全权威层，建议保留；
可做增量复核已验证前缀，但收益有限、复杂度高，未实施）；② 动画 ~20 s（`SIM_SPEED=50` 可调，
不影响预检判定）。若接受碰撞检出粒度放宽到 5 mm（极速档），终检与细查还能再减半——
**默认不做**，需要时再议。

## 7. 风险与回退

- 回退：`tools/traj7_make_original.py` 可从补丁版逐块还原原版（已验证：58,569 B、编译通过、
  与存档原大小一致）；建议还原后自行另存一份基线副本。
- 缓存正确性边界：键 = 起点关节(round 0.001) + 目标位姿(round 1e-6) + 参数；关节限位不进键
  （单次预检内限位不变，且 `_enable_obstacle_checks` 入口清空）。
- 粗筛短路的正确性依赖「10 mm 采样点 ⊆ 1 mm 采样点」（RoboDK 按等距参数采样成立）；
  若未来 RoboDK 改变采样方式需复核。
- 临时产物（保留备查，删除需确认）：`_traj7_baseline.log`、`_traj7_optimized.log`、
  `_traj7_trace_stdout.log`、`_traj7_trace.log`、`_traj7_seeds.txt`、`_traj7_orig_repro1/2.log`、
  `_traj7_original_repro.py`；工具：`tools/traj7_baseline_run.py`（可带脚本路径参数跑任意版本）、
  `tools/traj7_verify.py`、`tools/traj7_trace_run.py`、`tools/traj7_make_original.py`、
  `tools/traj7_singlepoint_smoke.py`。
