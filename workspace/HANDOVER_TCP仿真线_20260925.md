# HANDOVER — TCP 仿真线（2026-09-25 本窗口成果 + 待办：黄色轨迹）

> 给下一个窗口：本文是 **`机械臂TCP仿真.py` 路径预演优化线**的完整交接。
> 本工作区另有一条独立的伺服零点线（见 `AGENTS.md`），与本文件无关，勿混淆。
> 本窗口全部结论均出自实机仿真实测（RoboDK 6.0.2 + CR5 工作站，RunMode=1）。

---

## 1. 一页摘要：本窗口完成了什么

1. **优化已实施并验证**：对 `机械臂TCP仿真.py` 打了 11 个补丁块（预检函数内部），
   `连续轨迹7.json`（11 原始点→17 执行点）实测：
   - 整段预检 **285.4 s → 96.1 s（约 1/3）**；总耗时 **305.8 s → 116.2 s**
   - `_linear_path_endpoint`：67 次全算 189.8 s → 实算 34 次 29.4 s（缓存命中 31 次）
   - 兜底选解 `_obstacle_joint_target`：24.5 s → 11.0 s
   - **最终计划与执行轨迹 17/17 点逐点一致**（方法+每点 J6 目标全同，`tools/traj7_verify.py`）
   - 分支失败序列与原版复跑逐项相同（P11,P11,P8,P11,P8,P15）
2. **三个优化点**（判定粒度不变）：① 终点提取 `InstructionListJoints` 改 COLLISION_OFF（碰撞判定仍由同路径 1mm MoveL_Test + 整段终检负责）；② 四个纯函数加 `_plan_cache` 结果缓存（`_enable_obstacle_checks()` 入口清空，生命周期=单次预检）；③ MoveL_Test 先 10mm 粗筛失败即拒（粗采样点⊆细采样点），通过段仍跑 1mm 细查。
3. **原版可精确回退**：`tools/traj7_make_original.py` 从补丁版逐块还原原版 → `_traj7_original_repro.py`（58,569 B，与存档原文件大小**逐字节吻合**，编译通过）。
4. 完整技术文档：`TCP仿真路径预演优化.md`（结构解读/实测数据/补丁明细/等价性验证/风险回退）。
5. 用户疑问已答（本窗口为何"忙碌"）：验证链共跑了 **7 次完整 RoboDK 仿真流程**（基准 305 s、优化复测 116 s、逐调用诊断 138 s、原版重建 ×2 各 ~294 s、单点冒烟 2 s、轨迹颜色探针），每次 2–5 分钟墙钟，非卡死。

## 2. 当前文件状态（工作区根目录）

| 文件 | 状态 |
|---|---|
| `机械臂TCP仿真.py` | **已打补丁**（62,151 B，md5 `6523d32588385606527d4ff7d837ed46`）；启动日志含「预检带结果缓存与MoveL粗筛」 |
| `_traj7_original_repro.py` | 逆向重建的原版（58,569 B，md5 `21a2cee26453e9724b5c700df5873e6f`）；回退时直接覆盖回去 |
| `TCP仿真路径预演优化.md` | 本线权威文档（已交付） |
| `连续轨迹7.json` | 测试轨迹：11 点（P4/P9 特异点，y=-775/-762 工作位） |

工具（`tools/`）：
- `traj7_baseline_run.py` — 无头 runner：AST 原样提取脚本全部函数注入执行，与 GUI「执行」按钮同路径；**可带参数跑任意版本**（如 `python tools\traj7_baseline_run.py _traj7_original_repro.py`）。跑前确保 RoboDK 已开且 CR5 工作站已加载、起始关节为 q0（见下）。
- `traj7_verify.py` — 基准/优化日志对照（判定行 + 执行段逐点）。注意：PowerShell 重定向日志是 **UTF-16 LE**，脚本已处理。
- `traj7_trace_run.py` — 逐调用跟踪版（LIN#/OBST# hit/miss）。
- `traj7_make_original.py` — 补丁版 → 原版逆向重建（含全部 11 块原文）。
- `traj7_singlepoint_smoke.py` — 单点选项卡冒烟。
- `rdk_timing_probe.py` — 单 API 计时探针（上一窗口）。
- `trace_color_probe.py` — **黄色轨迹任务探针（本窗口新增，见 §4）**。

日志（临时产物，删除需用户确认）：`_traj7_baseline.log`（305.8 s）、`_traj7_optimized.log`（116.2 s）、`_traj7_trace_stdout.log`/`_traj7_trace.log`/`_traj7_seeds.txt`（诊断）、`_traj7_orig_repro1/2.log`（原版对照 294 s 级）。

关键环境数字：起始关节 q0=[-16.38, 0.936, 91.282, -2.218, -90.0, 73.62]；`SIM_SPEED=50`；障碍物 `安装台_650x650x80mm`、`地面_禁止穿越` 必须在站内；本机 python 3.13 无 numpy；`Mat` 无 `.Valid()`（Item 有）。

## 3. 补丁要点（下个窗口若要改/审）

- 缓存基础设施在模块顶部（`_plan_cache`/`_cache_key_joints`/`_cache_key_pose`/`_movej_test_cached`）。
- `_linear_path_endpoint` / `_obstacle_joint_target` 拆成缓存壳 + `*_uncached`；`_checked_j6_rewinds` 生成器→缓存列表（两处调用点均为 for 迭代，兼容）。
- **缓存副作用契约**（已核对）：调用方对返回列表只读或拷贝（`end[:]`/`dict(joints=end[:])`）；`_movej_test_cached` 命中且结果为成功时用 `setJoints(end)` 复现"关节停在终点"副作用。
- 裸 `robot.MoveJ_Test` 仅剩缓存包装内部 1 处；碰撞开关只改了终点提取一处，`_verify_obstacle_plan`（整段权威终检）仍 COLLISION_ON + 1mm，**勿动**。
- 已知可接受差异：缓存命中后「MoveJ快速筛选…」日志只打一次（原先同目标重复 4–5 次即重复搜索副产物）。

## 4. ★ 待办：把实际运行轨迹改成默认黄色曲线（用户已明确要求，未开始）

**用户原话（重复了多次，重视）**：「把路径预演后的机械臂仿真实际运行轨迹改成默认的黄色曲线」。

**现状与锚点**（补丁版行号）：
- 实际运行轨迹显示 = RoboDK 内置 Trace：`execute_recorded_trajectory` 内
  L1214 `RDK.Command('Trace','Off')`、L1215 `Reset`、L1220 `Reset`、L1221 `On`、L1247 `Off`（finally）；
  单点路径 L380–386 同一套。
- 脚本本身不画曲线，全靠 Trace。

**本窗口探针实测**（`tools/trace_color_probe.py`，Trace On + MoveJ 8° + 等 0.5 s 后）：
- ⛔ **站内没有任何 Trace 曲线对象**：`RDK.ItemList()` 全表 23 项（站/程序/机器人/工具/P1/物体/摄像机），
  无新增曲线；按名 `RDK.Item('Trace'|'TCP Trace'|'轨迹', ITEM_TYPE_OBJECT)` 均无效。
  ⇒ RoboDK 6.0.2 的 Trace 是**显示层叠加**（或对象名/时机未命中），拿不到对象就 `setColor` 不上。
- 站内既有对象快照已存档于本文件（类型码：程序=10、机器人=2、Base=3、工具=4、物体=5、目标=6）。
- 探针结束时关节已复原 q0。

**候选路线**（下个窗口按序试，先低成本后高成本）：
1. **GUI 设置路径（最可能"默认黄色"所指）**：RoboDK 菜单 Tools → Trace（轨迹）设置里有颜色选项，
   默认即黄色。让用户在 GUI 里把颜色改回默认黄即可，**可能根本不用改脚本**。
   先问用户/看设置（下个窗口有 GUI 可看）。
2. **`RDK.Command('Trace', ...)` 其他子命令**：试 `RDK.Command('Trace','Color <r,g,b>')` 之类
   （签名未知，需试；RoboDK 文档只保证 On/Off/Reset/Clean）。逐个试并观察 GUI。
3. **Trace 对象时机/名称再探**：Trace On → 完整动画 → Trace **Off 之后**再列 ItemList
   （本探针在 Trace 仍 On 时列的表）；以及列 robot 的子项。
4. **自绘曲线（保底、可控）**：Trace Off，改为在 `execute_recorded_trajectory` 执行循环里
   按实际关节采样（每步 Move 后 `robot.Joints()` 或直接用 plan 关节——脚本每步已校验
   实际=预检到 0.1°），`RDK.AddCurve(points,...)` 建曲线对象后 `curve.setColor([1,1,0])` 置黄、
   加入站并在 finally 清理。⚠️ AddCurve 参数（参考系/ADD 标志）需探针验证；
   黄色 RGB 建议 [1.0, 1.0, 0.0]（纯黄）或与 GUI 默认取色一致。
5. **RoboDK.ini 持久化**：若 Trace 颜色存在配置文件里，可一次性改配置（找到 `%APPDATA%/RoboDK/` 下
   ini 的 Trace 相关键）。

**注意**：用户说"**默认**的黄色"——大概率指 RoboDK 自带 Trace 的默认黄，优先路线 1/2，
不要急着上自绘曲线（那是行为改变，需用户认可）。

## 5. 方法论红线（本线适用，沿承工作区纪律）

- 改含中文文件**只用 `edit`/`write`/`apply_patch`**，禁 PowerShell 改写（历史 mojibake 事故）；
  本文件本身也如此。
- 任何检测/搜索先做**正例自检**；`apply_patch` 对 CRLF 文件要带 `\r\n`（本脚本磁盘为 CRLF，
  补丁块曾因此整体失败一次，未损坏）。
- 验证纪律：跑前基线、跑后同层校验、如实报告；长仿真用 `exec background` + 日志轮询，
  每次全流程 2–5 分钟，**预算好等待次数再动手**（本窗口 7 次即用户感知"忙碌"的原因）。
- 不碰真机：本线全部 RUNMODE_SIMULATE；RoboDK 连接走本机 API（上一线 29999/驱动进程的事已关闭，勿重启）。

## 6. 下一个窗口建议第一步

1. 读本文件 + `TCP仿真路径预演优化.md`（细节都在后者）。
2. 处理 §4 黄色轨迹：先让用户确认 GUI 里 Tools→Trace 的颜色现状（或直接试路线 2 的 Command 变体，
   快速可逆）；如走路线 4，先写 `tools/trace_curve_probe.py` 验证 AddCurve+setColor 再动主脚本。
3. 承前积压（低优先，与用户确认后再动）：临时 `_traj7_*.log`/`_traj7_original_repro.py` 清理（须确认）；
   伺服线现场复验（见 `AGENTS.md` §19.4，需用户在场）。
