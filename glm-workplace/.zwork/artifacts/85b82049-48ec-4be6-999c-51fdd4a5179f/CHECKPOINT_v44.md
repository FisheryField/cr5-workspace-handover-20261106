# CHECKPOINT_v44（2026-10-10 晚 · v14j 落地版）

> 接 v43 检查点摘要（对话内）。v40~v43 未落盘，本文件为其合并对应物 + v14j 落地记录。
> 本轮完成了此前两轮悬置的检错闭环：探针坐实 → v14j 三处修复 → 离线全绿 → 站内宏已刷。**未动实机。**

## Goal
- Dobot CR5（192.168.5.1，root/dobot）+ RoboDK，跑通连续轨迹7（11 录入点→17 执行点，E7/E15 两个 ±180 奇异换向）。
- 活跃主线：`sim_scripts\TCP真实运动_P2P版.py`（P2P 版宏，MoveJ 直达优先+避障预检）。
- 版本谱系与死点定位详见 `v14版本谱系与死点定位.html`（已随 v14j 更新）。

## 本轮定案（证据链完整）
1. **E15 死因改判**——不是"前视被覆盖"单一原因，真凶是 v14d 反方向坐标算错：
   - `probe_p14_lookahead.py`（插桩版）15/15 种子全量输出：多数种子在 P14 前视拿到「-180:限位OK、FKTrue、碰0」构型（如 `[86.9,69.7,-27.7,48.0,-90.0,176.9]`→J6=-3.1° 活路），P15 仍报"两方向均碰撞"且**无任何救援日志**。
   - 源码对读：`alt[5] -= 2 * delta`（L1453/L1473）算出 q−360°（朝向未翻转，FK 必拒）而非 q−180°。**一行算术错误杀掉全部种子。**
2. **帮凶一**：v14f 切分支救援枚举基准用翻转后 `target`，候选再 ±180 回未翻转位姿，FK 永不匹配——结构性死代码。
3. **帮凶二（仅种子 13 路径）**：前视选对族后弧碰退 MoveL，连续选解锁回当前族——"前视被覆盖"推断坐实，但只是少数路径。
4. **TCP仿真 为何能过**：它没有步内救援梯子，靠外层 (种子×J6方向组合) 枚举 + failed_prefixes 重试；P2P 把"换方向"压进步内梯子时第一级就写错了。
5. **撤销项**：原 v14j 计划中"E11 肘高排序"“前视视界扩到下一奇异点"两顶不需要——v14i 前视已 15/15 选到可翻转族。

## v14j-20261010-2030 改动清单（8 处补丁）
1. LOG_VERSION / root.title / 启动 log 行（三处版本标识）。
2. **主修复**：L1453/L1473 `alt[5] -= 2*delta` → `-= delta`（超限反方向 + 碰撞反方向两处）。
3. **v14f 位姿基准**：`_ik_branch_candidates(target, q)` → `_ik_branch_candidates(_trajectory_pose(q), q)`。
4. **前视绑定执行**（新块，note='前视绑定避障直达'）：前视构型弧碰时不退 MoveL、不走 v14c 无资格救援，只换用其他前视合格分支直达，全失败则本构型判死整段换种子。`lookahead_ok` 循环顶初始化为 None。
5. v14g"MoveL到场再换向"同款位姿奇偶问题**留档未改**（主修复后不触发；若未来触发按 v14f 同法修）。

## 验证状态
- **2026-10-12 10:28 v14j 实机全通过：轨迹 7 17/17 点全程跑完**（10:24:29 启动→10:28:06 完成；E7/E15 换向、MoveL 细分段、IK 分支救援全部实测走通）。日志：real_gui_log_p2p.txt 10-12 10:24~10:28 段。
- **2026-10-12 10:40 v14k-20261012-1040 落地**：停用长运动分瓣（split_moves 恒 False，一行改动+注释留档）。依据=当日实测：假断连与跨度无关（20mm 途经点也每条断），分瓣只剩每瓣停顿税；断连容忍器 20s 静止上限罩得住单指令收尾（180°≈9s）。MoveL 细分途经点保留（驱动 MOVL 已判死，不能发）。ast 过、离线 verify 零回归（输出与 v14j 逐行一致仅版本号更替）、站内宏回读 v14k。**v14k 未上机**，需实测验证不分瓣连续段收尾。
- 此前：ast.parse 过；`verify_v14c_plan.py` **离线全绿：种子 1 直接过 17 段**（E7 换向+180°→+0.0°；E15 换向-180°→-3.1°；E11 救援 +169.2° 族）；v14j 已刷站内宏并回读确认。工作站未保存（铁律）。

## Next Steps
1. **用户上机重跑轨迹 7 验证 v14k**（零位出发；预期无"长运动分瓣"日志行、连续段一指令直达、总时长明显缩短；跑完下使能+切模式清队列再断电）。
2. v14k 实机通过 → v14 主线收口 → 回 v13 reswap（ast.parse 先行）。若 v14k 露出真断连指纹（未自然收尾/未到位），回滚方法已写在代码注释（split_moves 一行改回）。
4. 延后池不变：homeEncoder 第 4 条核验、P1 重建、unio FoE（2.3.2.0≠2.3.4.1）、0x83、09:32 报警链、0x92 复盘、监控重启（须删 STOP_HOMING_POLL 哨兵）。
5. workspace Memory 更新因服务端连续超时未落盘（2026-10-10~12 五次失败）：内容快照=工作区根 MEMORY_PENDING.md，服务恢复后照文 supersede 并删除该文件。

## Critical Context
- 磁盘 `sim_scripts\TCP真实运动_P2P版.py` = v14j-20261010-2030（~92KB）。
- 嵌入式 python：`D:\software\RoboDK\Python-Embedded\python.exe`。
- 探针/取证资产：`probe_p14_lookahead.py`（本轮立功，插桩 wrapped_lookahead 打印候选+实际返回）、`probe_p11_collision.py`、`probe_e11_branches.py`、`dump_expanded_records.py`、`confront_e14_configs.py`。
- 轨迹源：`D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹7.json`。
- RoboDK 站：活动站"新建工作站 (1)"（未保存恢复站），站内宏已 = v14j；残留 `_probe_P11` 空程序无害。
- 实机态（17:29 最后 GUI 日志）：模式 5、六轴≈0、速度零。
- 铁律：SSH 一律 `tools/rssh.py` 且复杂命令落 .sh；写盘须用户批准；使能/标零/实跑归用户；绝不保存工作站；ast.parse 先于 reswap。
- API 踩坑累积：edit/apply_patch 失败是原子的、oldText 必须逐字（本轮再踩一次：错字导致 3 hunk 全回滚）；RoboDK SolveFK 对超限关节抛 TargetReachError（限位先查）；ask_user_question plan-review 必带 detail；PS 内联避免中文+嵌套引号。
- 三套坐标指纹/报警码/0x86 机理：见 CHECKPOINT_v37.md 及 workspace Memory。
