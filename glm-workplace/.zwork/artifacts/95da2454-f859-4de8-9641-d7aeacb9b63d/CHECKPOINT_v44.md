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
- **P2P 宏已回退 v14k（2026-10-12 15:00）**：磁盘母本与站内均 = v14k-20261012-1040（92562 字节，ast OK）；v14l 全量备份在 `sim_scripts\TCP真实运动_P2P版_v14l_20261012-1117.py.bak`（96866 字节）；MOVL_TRIAL_MAX_MM/_movl_trial_ready 已随回退消失；verify_v14c_plan 离线预检全绿（指纹与 v14j/k/l 基准一致：种子 1、17 段、段 5/9 MoveL 细分 6/4 点、段 7 +180°、段 11 分支救援、段 15 -180°）；refresh+probe 回读确认。v14k 母本源=rdk_station_dump\tmprtki6ho6\verify_v14a.py（10-12 10:41:42 实机通过后站内导出）。
- **v14k 复跑成功（2026-10-12 下午，用户实机）**：回退闭环 + 臂脱困 + GUI 未再闪退（同一 ensure_connected/_prepare_real_plan 路径跑通，闪退与 v14l 代码无关——diff 未触及两窗口，更像与昨日臂困/报警态相关，待办降级为观察项）。
- **v14k→v14l diff 复盘定案（diff_v14k_v14l.txt，12 hunks）**：致命变更仅一处——执行层短直线段≤150mm 丢途经点直发驱动 MOVL（P5 生效）；护栏拆降（MoveL 无途经点 ValueError→log）本次未触发非致错路径；其余 9 处为开关基础设施/无关注释。错不在代码 bug（精确执行了设计），在设计假设：把 v13 断连当假断连重试，实际是驱动 MOVL 无工具补偿的语义错位；碰撞预检背书的是意图（命令 TCP 直线安全）验证不了执行语义（法兰目标横偏 154.8mm）。代价换来死因从现象（断连）并到机制（无工具补偿）。
- **2026-10-12 14:14:00 上电使能事故定因（日志实证，非 0x86 老病）**：时间线：14:13:07 冷启动→14:13:52~56 上电自检（touchButton_4 m_powerCnt 1→9、LED 蓝转绿中）→**14:14:00.010 使能被接受时 controlMode_enable, m_powerFinish=false, dragMode=1**（上电流程未完成+拖动模式残留）→30ms 内六轴齐报 SoftMotion"2 axis error"/伺服错 12832(0x3220)→EtherCAT 退出 OP(60945)+0x83 末端IO掉线→**0 秒强制下使能（下坠：J2 -45.8°→-36.6°+9.2°重力下垂）**→14:14:00.638 uiBodyVolt=207.bBodyPowerFlag=1->0→gPowerDown=true（断电）→14:14:01.5 起 DataAlarmPowerGoodErr 循环 14s+EtherCAT slave 数变化→**14:14:54 GController 整进程重启**。**关键负面证据：无 0x86；homeEncoder.json 无新写入（末条=10-10 16:56:39 全 true，零点基准未动）；重启后 PoseTrace 三列同系吻合（-69.5,-36.6,-50.2,-85.0,-69.7,-180.1）。** 结论：使能时机非法（上电未完成+拖动模式）→驱动拒绝使能→总线塌→重力下垂→电源 Good 故障下电。隐患待查：uiBodyVolt 207V 偏低（使能转矩冲击下流轨是否欠压）。取证脚本：probe_cabinet_after_power_drop.sh、probe_cabinet_death_window.sh。当日前置：12:11:49 急停（0x74+0x7e，长使能 6436s）。
- **2026-10-12 11:30 v14l 试航实机判决：失败，死因升级为“驱动 MOVL 无工具补偿”**（比 v13 的断连指纹更深一层）：P5 直发驱动直线后停在中途（已完成 4/17），停机时**法兰位姿=命令的 TCP 目标位姿（差仅 5.5mm）**，真实门把手尖端多探出一个工具长（159.63mm），停在 (103.4,-929.8,300.4)、距圆柱轴 106.7mm<R180（进入模型包络，RoboDK 碰撞图标红）；认证直线本身离柱最近 199.9mm 安全。关节分数 J1/J5≈40%、J2/J3/J4 为跨度 6~8 倍坐实“驱动走向完全不同构型”。翻转分支假说已拒（15 分支最小失配 6.94°）。探针：`probe_movl_stop_geometry.py`、`probe_movl_branch_flip.py`、`probe_movl_tool_offset.py`。**v13 死刑维持且定性升级：当年断连指纹的本源=驱动把 TCP 坐标当法兰目标，落到完全不同构型→“到位”永不到来。细分途经点是关节目标（MoveJ 与工具无关）客观上绕开该缺陷——它是正确工程答案，勿再删。** 宏注释已补死因（v14l 开关留档默认关，仅供复现）；用户现场处置：目视是否真接触→目标关节模式移回/示教器低速移出→重启宏不勾试航重跑。
- **2026-10-12 10:47 v14k 实机全通过（轨迹 7 17/17，2:58）**：零分瓣日志行、总时长 3:37→2:58；但 P5/P9 两段 MoveL 细分（6/4 跳×20mm×每跳~3s 停顿）成为新效率瓶颈——用户观感即"分瓣"，实为 v13 方案B 细分途经点。
- **2026-10-12 11:17 v14l-20261012-1117 落地（MOVL 试航开关，默认关）**：依据=v13 判死驱动 MOVL（3 断连指纹+pyc 反汇编）发生于假断连容忍器成熟之前，而 10-12 实测每条 MoveJ 也假报断连且容忍器 60+ 次全扛。机制：GUI 复选框（默认关）勾上后，≤MOVL_TRIAL_MAX_MM(150mm) 的 MoveL 段在执行层跳过细分途经点直发驱动直线；段长用 `_trajectory_pose(end)*invH(_trajectory_pose(expected))` 欧氏距离；离线 verify 无 GUI 变量自动回 False（零影响）；执行循环在 expected 链上判定；异常指纹（断连/未到位/落点偏差）自动提示去勾回退；单点 MoveL 同款试航。路径安全不变：MoveL_Test@1mm 预检+整段 1mm 带碰撞复核验的一直是真直线，途经点只是执行细节。ast 过、离线 verify 两次零回归（仅版本号变化）、站内宏回读 v14l。**v14l 待上机：勾选试航重跑轨迹 7。**
- **2026-10-12 10:40 v14k-20261012-1040 落地**：停用长运动分瓣（split_moves 恒 False，一行改动+注释留档）。依据=当日实测：假断连与跨度无关（20mm 途经点也每条断），分瓣只剩每瓣停顿税；断连容忍器 20s 静止上限罩得住单指令收尾（180°≈9s）。MoveL 细分途经点保留（驱动 MOVL 已判死，不能发）。ast 过、离线 verify 零回归（输出与 v14j 逐行一致仅版本号更替）、站内宏回读 v14k。**v14k 未上机**，需实测验证不分瓣连续段收尾。
- 此前：ast.parse 过；`verify_v14c_plan.py` **离线全绿：种子 1 直接过 17 段**（E7 换向+180°→+0.0°；E15 换向-180°→-3.1°；E11 救援 +169.2° 族）；v14j 已刷站内宏并回读确认。工作站未保存（铁律）。

## Next Steps
1. **用户现场处置（最高优先）**：目视门把手尖与圆柱是否真接触；未接触则宏“目标关节”模式（纯关节 MoveJ，带弧碰撞预检）移回 P4/零位，或示教器低速移出；随后重启宏（**不勾 MOVL试航**）重跑轨迹 7 验证回退全绿；收尾照铁律。
2. v14l 试航证据归档：三支探针（stop_geometry/branch_flip/tool_offset）+日志 11:30 段；v13 死刑维持，细分途经点定为永久方案，不再重审 MOVL。
3. v14k 已全通过 → v14 主线收口，可回 v13 reswap（ast.parse 先行）。
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
