# 上下文检查点摘要（CR5 机械臂项目 · 会话续接用，第 37 版）

> 第 36 版后重大进展：**3.2.d.8 首次使能全绿（14:32:44 起 stable、三列 PoseTrace 首次同系吻合、零报警）**——"报警后上电使能必下坠"以换固件闭环。**根因对比已完成三层闭环**（总线抓包 A/B + 刷机 A/B + 反汇编定位），定论=3.1.5.0 驱动定零易失。另发现工作区根 `HANDOVER.md`（另一会话 12:00 归档，已加过期横幅）并吸收其独有约束；**已存 workspace Memory**（新会话自动召回）。**当前等用户决定是否开始 3.2.d.8 重新标零。**

## Goal
用户在 `D:\mydata\glm-workplace` 调试 Dobot CR5。两条线：
- **当前活跃线**：3.2.d.8 使能已成功但显示系≠物理姿态 ⇒ 需重新标零 → 核对 homeEncoder.json → 重建 P1 → 才能恢复一切运动。
- **挂起主线**：站内宏 `TCP真实运动` 安全驱动执行 `连续轨迹7.json`；v13 补丁已全部落码，等用户确认后 reswap（**坐标判据需按新系重建后才放行实机**）。

## Constraints & Preferences
- **伺服固件=3.2.d.8**（用户 9/28 自刷，settVersion 14:22:27 六轮确认；"保持 3.1.5.0"约束作废）。
- **写操作须用户批准**；SSH 全程只读取证；**使能/标零等动手环节归用户**（安全要领：人站侧后方、手扶急停、使能后静止 30 秒、抱闸毫米级下沉正常）。
- **⛔ 重新标零前禁止调用任何已存点位/轨迹**（P1、轨迹7、v13 宏）——当前显示系下全是错误位置。
- **⚠️ 标零-主控版本约束（3.1.5.0 实测，3.2.d.8 未验证）**：补丁主控 `9a808cd9…` 下标零死在 `HomeNumdone:2`；须原版主控 `8416cf0e…` 才能走完 0→2→4→6。**当前主控=补丁版 ⇒ 下次标零前先决定是否回退原版主控+重启（回退/装回都要用户批准）。**
- 控制器零改动；绝不保存工作站；用户 JSON 与磁盘 `机械臂TCP真实运动.py` 只读；补丁只进 `sim_scripts\`；母本=`sim_scripts\TCP真实运动_升级版.py`。
- read/ls 仅限工作区；外部文件用 exec/python/rg；PS 5.1 嵌套引号/`$` 必炸。
- **SSH 通道**：一律 `tools\rssh.py`（root/dobot@192.168.5.1；`-f 脚本.sh`/`--put`/`--get`）；⛔ 复杂命令必须落 .sh；BusyBox ash（`ls -le`，无 curl 用 `wget --post-data`）。
- 顺序铁律（主线）：ast.parse → 用户看改动说明 → 用户确认 → 才跑 reswap；宏不热更新，reswap 后关旧窗重开。

## Progress
### Done（本轮新增，接 v36）
- **① 3.2.d.8 首次使能全绿**：14:32:39 CheckEnableDirection（全史第 4 次）→ 按钮期间给定自走 ±0.8°、实际紧随（新固件整定动作，非翻系）→ 14:32:44.096 `robot enabled`、LED 绿 → 采集时点(+23s)仍 enabled 无任何 disabled 行；AlarmSysSetBit/logServoError/0x82/0x83/60948/60949 全零。**三列 PoseTrace 首次同系吻合**：nextPos=0x6062=gActual 逐帧一致、稳态偏差<0.001°（对比 3.1.5.0 三次使能全翻系+0x86+≤3.3s 掉）。
- **② 使能后状态记录**：稳定关节=92.242/18.097/155.730/-71.652/-143.843/-0.417（对应笛卡尔 64,-269,113 ≠物理位置）；homeEncoder.json 未被重写（md5 仍 3c37…8961）；0x6064 使能态=6733/29536/21805/8810/20648/4839（vs 掉使能态五轴各移~2500 计数、J6 不动）；0x607C 全 0。
- **③ 根因定论（三层证据，归档 baseline §11）**：总线抓包（9/22-23 存量证据）证明 `/calibrate/home` 两版主控命令逐字节相同、差别全在驱动器——3.2.d.8 的 0x6064 跟随 0x607A 归零且持久；3.1.5.0 不跟、下使能短暂归零、**上使能即弹回旧值（易失零点）**。刷机 A/B（同主控/同档案/同姿态）唯一变量=固件，判定成立。因果链：定零易失→报警/断电后零点退回上电相对零→主控给定与驱动零基准错位→使能瞬间朝错误位置发力=下坠/晃动→假偏差>5°→0x86 强制下使能。homeEncoder.json 全零记录=同根因另一表现（calihome 回调应答不可靠）。
- **④ 续接机制建成**：存 workspace Memory 一条（新会话自动召回）；`HANDOVER.md` 顶部插入过期横幅（防误读，同时指路）；生成本 CHECKPOINT_v37.md。
- **⑤ 吸收 HANDOVER.md 独有信息**（3.1.5.0 时代另一会话成果）：上述主控-标零约束；`SteadyErrorThreshold` 已改 1.0×6（两路径+重启已生效）；`0x607D` 软限位=[0,65535] 窗口窄、`H01.17 编码器位置角`=0 六轴、`loadParams.json` loadValue=0.2kg（碰撞误报嫌疑）、碰撞五档方案 `COLLISION_AVOIDANCE_PLAN.md`、unio FoE 刷写 4 连败（errcode 28673）、位置换算 counts×1.782178e-4=°、报警码表 87+543 条本地 `data/alarm_*.json`。
- **⑥ 发现存量逆向资产**（后续别重复造轮子）：`D:\mydata\codex\b\`（fw315/fw32 payload、`dobot-evidence-20260922\` 四份报告+pcap）；`D:\mydata\workspace\ZERO_CHANNEL_3.2.D.8.md`（总线级解剖：PDO 布局/邮箱解码/两版归零对照）；`D:\mydata\workspace\tools\ecat_*.py`（抓包分析脚本）；`D:\mydata\working things\机械臂控制柜数据\`（3.1.5.hex、3.2.D.8 hex 等）。
- **⑦ 本轮新文件**（`sim_scripts\`）：`diag_fw_locate.sh`（固件文件定位）、`insert_handover_banner.py`（已用完可留档）。

### In Progress
- 等用户决定：开始 3.2.d.8 重新标零（先定主控版本问题，见 Constraints）。

### Blocked
- 主线 v13 reswap：坐标判据（J5=-40 系、P1、轨迹7）全部要按新系重建后才可放行实机。
- 长期隐患：unio 2.3.2.0≠期望 2.3.4.1（FoE 刷写 4 连败，mailbox error:2040×64）——**3.2.d.8 下依然在，总线抖动仍会报警断使能（只是零点不再丢）**；09:32 首次报警链源头未定；0x83 末端IO线缆；`TryLockForRead#41 lock_num:-1` 未解读。
- 旧：9090 DobotLink 杀不死；`tools/servo_zero_fix.py` 缺失。

## Key Decisions
- **"报警→使能下坠"以固件更换闭环**；根因=3.1.5.0 定零易失（指令级定位不做：94% 字节重排、无符号表、不改变处置结论，封存）。
- **innerEncoder 只是标定时刻 0x6064 快照、不参与运算**（在线反证：非零 innerEncoder 时关节读数仍为 0）；关节角=0x6064×scale。
- **使能判据（新）**：三列 PoseTrace 同系吻合 + enabled>30s + 零报警 + 面板读数与物理姿态吻合（四项）。
- **显示系现状**：3.2.d.8 稳定值族 `92.2/18.1/155.7/-71.7/-143.8/-0.4`（≠旧定基系≠旧原始系）；刷机重置了驱动计数基准。
- 沿用：改盘上配置须用户显式批准；动手环节归用户；不保存工作站；B 方案轨迹细分（20mm/300mm）；MoveL 驱动死刑；双保险丝；SSH 走 .sh。
- **交接机制**：新会话信息源=workspace Memory（自动）+本文件+`sim_scripts\flash_32d8_baseline.md`；HANDOVER.md 只当历史资产用。

## Next Steps
1. **标零前决策（问用户）**：3.2.d.8 下用补丁主控标零是否仍死在 HomeNumdone:2 —— 建议**先回退原版主控 8416cf0e→重启→标零→装回补丁版→重启**（回退/装回均需批准；也可先在补丁版下试一次，死了再回退，代价是多一轮重启）。
2. 用户执行标零（enable 状态、机械对齐姿态）→ 我盯日志 `HomeNumdone 0→2→4→6` + `servo calihome done`。
3. **标零后立即核对**：homeEncoder.json 新记录（值合理非全零、日期正确）+ 掉使能/再上电后 0x6064 是否保持归零（易失性复查）。
4. 重建 P1 存档 → 更新 v13 宏坐标判据（新系）→ 回主线 reswap 流程。
5. 建议跟进：unio 固件升级评估（FoE 4 连败需换通道或厂商）、末端 IO 线缆、TryLockForRead 观察。

## Critical Context
- **权威档案**：`sim_scripts\flash_32d8_baseline.md`（§1-8 刷机基线、§9 使能结果、§10 结论与警告、§11 根因定论）；使能取证脚本 `sim_scripts\diag_after_enable_32d8.sh`（12 节，可重复跑）。
- **三套坐标指纹**：①3.1.5.0 定基系 P1 附近=`163.6x,8.1x,97.5x,-1.9x,-90.0x,-106.3x`；②3.1.5.0 原始系=`8.34,20.00,2.60,20.99,15.79,19.89`；③**3.2.d.8 现行系=92.24/18.10/155.73/-71.65/-143.84/-0.42**（同一物理下垂姿态）。物理姿态：J2≈16.5°、J3≈100.6°（旧定基系度量）。
- **14:32 使能窗口锚点**：行 405515-405671；enabled@405639、LED 绿@405637；log 基线约 405770+ 行。
- **homeEncoder.json**：`/dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json`；现内容=单条 9/27 17:56:18 记录 innerEncoder=[204984,-988411,-877546,695220,-320522,608969]（3.1.5.0 计数，与新基准不同档）；备份：柜上 `.corrupt_20261010_114807`、本地 `sim_scripts/homeEncoder_corrupt_backup.json`。
- **主控版本**：现行=补丁版 `9a808cd9dd8f3aa6adaa4de1a34eb9b3`（/dobot/userdata/codesys/allST/Application.app）；原版=`8416cf0eee070a640702c077eb904b4e`（标零用，本体在柜上何处待查——HANDOVER 未记路径，回退前先找）。
- **SDO 只读通道**：`POST http://192.168.5.1:22000/settings/readServoParams` body `{"body":[{"key":"addr606400","servoNum":"J1"}]}`；真值在日志 readSDO 行（常在 "fail" 行）；24676=0x6064、24700=0x607C；slave：J1=3…J6=8。
- **时钟**：日志钟 Oct 10 ≈ 真实 Sep 28（快约 12 天）；文件 mtime/JSON 日期=真实日期。
- **控制器**：192.168.5.1，SSH root/dobot；进程 gcontrol、codesyscontrol（exe=/udisk/codesyscontrol (deleted)）、logServer、redis、smbd；日志 `/dobot/userdata/CR5_sys_files/project/logs/all/log`；`/dobot/userdata/project`→`CR5_sys_files/project` 符号链接；SlaveLog 单文件 `/dobot/userdata/SlaveLog`。
- **从站版本**：safeio 2.4.0.0、terminal 3.3.2.0、unio 2.3.2.0✗（期望 2.3.4.1）、feedback 2.3.3.0、algs 1.5.19、codesys 3.5.4、control 3.5.6.1。
- **报警表**：`data/alarm_servo.json`/`alarm_controller.json`（`tools/alarm_lookup.py` 按 hex、`tools/alarm_lookup_0x7e.py` 按 id）；0x74=急停、0x7e(126)=面板开关、0x82=通用IO掉线、0x83=末端IO掉线、0x86=上使能偏差>5°强制下使能、0x8612=位置给定超限、60948=SAFEOP、60949=可能掉线。**总线抓包可直接逐轴读固件版本字（TxPDO 块内 +42：0x32D8/0x3150），不依赖控制器显示。**
- **事件时间线（日志钟 Oct 10）**：09:32:42 总线报警断 2348s 长使能→10:03:44 使能 0x86 下坠→10:38:31 使能晃动无 0x86→11:48:07 恢复档案→11:48:45 断电→11:49:22 冷启动→**12:01:10 使能翻系 0x86（方案 B 判死）**→~14:00-14:21 用户刷 3.2.d.8→14:21:52 干净开机→**14:32:44 使能成功（现行）**。
- **v13 代码地图**（母本 `sim_scripts\TCP真实运动_升级版.py` 1810 行，LOG_VERSION `v13-20261010-1003`@L24）：L740-752 单点 waypoints；L~822 常量区（TRANSIT_DIRECT_MAX_MM=300/LINEAR_SUBSTEP_MM=20）；L945-970 执行循环细分；L1150 `_linear_waypoints`；L1268 复核防呆；L1388 循环顶 waypoints=[]；L1427-1443 规划层 300mm 分流；L1454 plan.append。站内宏仍是 v12b（reswap 未跑）。
- **进程/端口**：RoboDK PID 25228；驱动已停（29999/30004 空闲）；看门狗 pid 15888（`sim_scripts\watch_macro_log.txt`）；DobotLink 占 9090；DobotStudio Pro ×4。命令口 29999/30003/30004 同时刻单客户端。
- **轨迹 7 几何**（17 执行点）：(500,0,300)→(0,-775,300) 922.3mm→…作业面~713mm→(-500,0,300) 911.4mm；P1 MoveJ、P2/P4-P6/P8-P10/P12-P14/P16 MoveL、其余 MoveJ。
- **踩坑累计**：read/ls 工作区外拒→exec/python/rg；Windows ssh.exe 坏→rssh.py；PS 内联复杂命令给 SSH 必炸→.sh；PS 内嵌 python -c 炸→落 .py；rg 正则含单引号→整条单引号包；edit 长中文块易炸→最小 ASCII 锚点或 apply_patch；BusyBox ls 无 --full-time（用 -le）；设备无 curl（wget --post-data）；`grep -ac` 可扫二进制；ast.parse 必先于 reswap；报错 P 序号=展开号；`Mat` 行数 `len(m.rows())`；MoveL_Test 后 Joints() 可能全零→InstructionListJoints 取；Stop-Process 高权限→`Start-Process taskkill /F /IM xxx -Verb RunAs`；ask_user_question 普通选项即可；工具结果超限进 artifact（tool_result_recall 取，limit≤16384）。
