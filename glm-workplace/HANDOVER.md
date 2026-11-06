# HANDOVER — CR5 机械臂（零点 / 碰撞 / 运动验证）

> 归档：2026-09-28 ｜ 自包含 ✅ —— 不需要读之前的会话或其它目录

> ⚠️ **2026-09-28 14:45 横幅（另一会话后加）**——本档写于 12:00，以下结论已过期：
> ① "伺服最终必须是 3.1.5.0" → 用户已自刷 **3.2.d.8**（14:21 起生效），14:32:44 使能成功且健康；
> ② "零点已修好" → 12:01 使能仍翻系+0x86（档案恢复方案判死）；
> ③ 坐标判据已换新系（稳定 92.2/18.1/155.7/-71.7/-143.8/-0.4），旧 P1/轨迹7/v13 坐标判据全部作废，**重新标零前禁调一切已存点位**。
> 最新权威档案：`sim_scripts/flash_32d8_baseline.md`（§9-11 含根因定论）；交接摘要：`CHECKPOINT_v37.md`。
> 本档仍有效的资产：主控版本-标零约束（原版 8416cf0e 才能标零 / 补丁 9a808cd9 死在 HomeNumdone:2）、HTTP SDO 只读通道、报警码表、碰撞方案、unio FoE 刷写 4 连败记录。
> 场景一句话：**在伺服 3.1.5.0 上把零点修好、让机械臂能按一条十点轨迹稳定运动，并解决"末端作业时碰撞误报"**

---

## 1. 设备与环境

| 项 | 值 |
|---|---|
| 设备 | **Dobot CR5** 协作机械臂（控制箱 CR5-CC162） |
| 控制器 | **`192.168.5.1`**，SSH `root` / 密码 `dobot` |
| 架构 | NXP i.MX6Quad，Linux 4.1.15-rt18 PREEMPT RT，**BusyBox ash（没有 bash）** |
| EtherCAT 从站 | **slave 3~8 = J1~J6**（DS121 驱动器）；slave 2 = 通用IO板(unio)；0/1 = safeio/terminal |
| 伺服固件 | **3.1.5.0**（六轴，用户硬约束：最终必须是它） |
| 主控 | **3.5.6.1-stable-c3db2f8d3** |
| 从站固件 | safeio 2.4.0.0、terminal 3.3.2.0、**unio 2.3.2.0**✗、feedback 2.3.3.0 |
| 关键端口 | `29999` dashboard（RoboDK 用）、`30003` 命令 API、`30004` 实时反馈、`22000` HTTP（含 `/calibrate/home`）、`22002` mToolServer(FoE) |

**环境红线**：
* ⛔ **命令口 `29999`/`30003`/`30004` 同一时刻只允许一个客户端** —— 客户端在用时，第二个连接会被 `ConnectionAborted`；**不要反复探测**（会把 accept 队列堵死）
* ⛔ **Windows 的 `ssh.exe`/`scp.exe` 已损坏**（任何调用零输出 rc=255）⇒ 一切 SSH/SCP 走 paramiko

---

## 2. ★ 当前状态（2026-09-28 12:00 左右）

### 2.1 零点 —— ✅ **已修好**

```
伺服: 3.1.5.0（六轴）
主控: 补丁版 9a808cd9dd8f3aa6adaa4de1a34eb9b3  ✓（六轴 PDO 补丁，读 0x6064）
标零: 日志出现 HomeNumdone: 0 → 2 → 4 → 6 且 servo calihome done ...   ✓
六轴: gActualPosition = -0.000356, -0.061845, -0.016575, -0.004634, 0.003208, -0.000178
      ⇒ 全部 ≈ 0（最大 0.062°）  ✓✓
```
**关键**：**标零必须在【原版主控】下做**（`8416cf0eee070a640702c077eb904b4e`）——
**补丁版下标零会死在 `HomeNumdone : 2`** ✗（已实测复现多次）。正确顺序：

```
回退原版 → 重启 → （机械对齐）→ 上使能 → 标零（必须走完 0→2→4→6）→ 装补丁 → 重启 → 验收
```

### 2.2 配置改动（已生效）

| 文件 | 项 | 原值 | **现值** |
|---|---|---|---|
| `properties/AdvancedFunction.json` | `SteadyErrorThreshold` | 0.05 ×6 | **1.0 ×6** ✓（否则 P1 姿态下 J2=0.56°、J3=0.37° 会误报 249/250 ⇒ 自动下使能） |
| 同上 | `FollowError` | 0.05 ×6 | 0.05（**未动**；若出现 `Ferr` 类报警再看它） |

> 两个路径都要改，且要**重启**才生效：
> `/dobot/userdata/CR5_sys_files/project/properties/` 与 `/dobot/userdata/project/properties/`

### 2.3 碰撞配置（**未改** ✗ —— 方案见 `COLLISION_AVOIDANCE_PLAN.md`）

```json
// settings/function/collisionDect.json
{ "Level1": [101,101,101, 15.15,15.15,15.15],   "Level5": [20,30,20, 5,5,5],
  "level": 2, "mode": 3, "backDistance": 10, "value": true }
// settings/function/loadParams.json      ← ★ 疑为碰撞误报的根因
{ "centerX": 0, "centerY": 0, "centerZ": 0, "loadValue": 0.2 }    // 只有 0.2 kg
```

### 2.4 未决问题

| 问题 | 现状 | 说明 |
|---|---|---|
| **`0x82` 通用IO板掉线** | ⚠️ 报警（时有时无） | `unio` 板 **mailbox 通信坏**（`MBX slave:2 error:2040` ×64）；FoE 刷固件**连续失败 4 次**（`g_TempFoeWriteErrCode=28673`，重试 3 轮全败）；`2.3.2.0` 与 3.5.6.1 要求的 `2.3.4.1` 不匹配 |
| `H01.17 编码器位置角` = **0**（六轴） | 嫌疑 | 厂商默认 90、`servoCSV` 标定值 J1=352 / J2~J6=330；**本机六轴全 0** |
| `0x607D` 软件位置限位 = **[0, 65535]**（六轴） | 默认值 | 窗口只有 `[0°, +11.68°]` ⇒ 任何负角度都可能触发 `0x8612 位置给定超限保护` |
| `AfterColliisonTorqueLimitSwitch` = `true` | 语义待定 | 名字直译"碰撞后力矩限制开关"，可能是"作业中允许被顶住"的关键项 |

---

## 3. 一条命令确认现状（只读、安全）

```bash
# 版本 + 补丁 + 标零记录 + 六轴
ssh root@192.168.5.1 '
  md5sum /dobot/userdata/codesys/allST/Application.app
  grep -a settVersion /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -14
  grep -a "servo calihome done" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -2
  grep -a "PoseTrace: gActualPosition" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -1
'
```

**判读**：
* `Application.app` = `9a808cd9dd8f3aa6adaa4de1a34eb9b3` ⇒ 补丁已装 ✓
* `servo1..6 : 3.1.5.0` ⇒ 固件符合要求 ✓
* `gActualPosition` 六值 ≈ 0 ⇒ 零点有效 ✓
* **若 `Application.app` = `8416cf0eee070a640702c077eb904b4e`** ⇒ 是原版（此时**才能**标零）✓

---

## 4. 本次会话的成果（按重要性）

| # | 成果 | 关键证据 |
|---|---|---|
| **1** | **★ 把零点真正修好了** | `HomeNumdone 0→2→4→6` + `servo calihome done`；六轴 `gActual` 最大偏差 0.062° |
| **2** | **★ 查明"J2 读数 365°"的真因** | 主控显示 = **360° + 驱动器给定(`0x6062`)**；驱动器真值 `0x6064` 一直是干净的（11.66°）。**那一圈是主控侧加的** |
| **3** | **★ 打通了 HTTP SDO 只读通道**（主控 3.5.6.1 才有） | `POST :22000/settings/readServoParams` `{"body":[{"key":"addr606400","servoNum":"J2"}]}`；真值在日志 `readSDO#...` 行 |
| **4** | **★ 拿到厂商伺服报警码全表**（87 条） | `0x8612 位置给定超限保护`、`0x8611 位置偏差过大`、`0x8481 速度偏差过大`、`0x7180 电机过载`、`0x7121 电机堵转`…… |
| **5** | **★ 定位 `0x8612` 的候选判据** | 厂商参数 **`H0B.12 CSP位置指令增量过大阈值`（默认 3，范围 1~7）** + 只读计数器 `H0B.13` |
| **6** | **解决"J2 动不了"** | 根因：**驱动器的 `0x607D` 软件限位窗口太窄** + **主控坐标系多一圈** ⇒ 命令越界被拒 |
| **7** | **`test.py` 十点十段运动脚本**（含碰撞预检换解） | 见 §5、`test.py` |
| **8** | **搞清参考脚本"既避撞又能动"的机制** | **`SolveIK_All` 枚举全部逆解 → 按"肘部离台面高度"排序 → 逐个 `MoveJ_Test` → 取第一个通过的** |
| **9** | **修正两处 IK 用法错误** | ① `SolveIK*` 要的是**法兰位姿**（`PoseFrame()*pose*invH(PoseTool())`）② 单点 `SolveIK` 会拒绝任务，必须换解 |
| **10** | **碰撞避免方案** | 五层方案，见 `COLLISION_AVOIDANCE_PLAN.md` |

---

## 5. ★ 关键数据（拿去就能用）

### 5.1 对象 / 地址 / 换算

| 项 | 值 |
|---|---|
| **位置换算** | `角度(°) = counts × 360 / (20000 × 101)`（= counts × **1.782178e-4**） |
| 关键对象 | `0x6041` 状态字、`0x6040` 控制字、**`0x6062` 位置给定**、**`0x6063` 内部单位实际**、**`0x6064` 位置实际**、`0x607A` 目标位置、`0x603F` 故障码、`0x6060` 运行模式（**8 = CSP**）、`0x607C` 原点偏移、`0x607D` 软限位、`0x6098` 回零方法（**35**） |
| SDO key 格式 | `addr` + **4 位索引** + **2 位子索引**（如 `0x6064:0` ⇒ `addr606400`；`H0C.00`=`0x200C:01` ⇒ `addr200C01`） |
| 厂商参数映射 | `H<组>.<序号>` ↔ EtherCAT `0x20<组>:<序号+1>`（259 条全表：`data/servo_fw_samples/hparam_map.json`） |

### 5.2 报警码速查（厂商伺服表 `alarm_servo.json`，87 条）

| 码 | 中文 | 备注 |
|---|---|---|
| **0x8612** | **位置给定超限保护** | 处置"请输入正确参数" ⇒ **参数/给定问题** |
| 0x8611 | 位置偏差过大保护 | |
| **0x8481** | **速度偏差过大保护** | 堵转时必现（设定速度快 ≠ 实际 0） |
| **0x7180** | **电机过载保护** | 堵转时必现 |
| 0x7121 | 电机堵转保护 | |
| 0x7181 / 0x7182 / 0x7183 | 抱闸故障 / 制动电阻过载 / 上使能失败 | |

控制器侧（`alarm_controller.json`，543 条）常用的：
`0x60~0x6F` 关节N轴状态错误/状态下使能、`0x30~0x35` 关节N超速、`0x36~0x3B` 关节N位置超差、
`0x45` 关节3负向限位、`0x82` 通用IO板掉线、`0x86` 上使能关节位置偏差过大（**>5° 硬编码，强制下使能**）、
`0xF9/0xFA` 第二/三轴稳态误差过大、`0x74` 急停、`0x7E` 面板开关

### 5.3 碰撞相关接口签名（解自 `gcontrol`/`libdataSvr.so` 符号，比文档准）

```
SetCollisionLevel(int, bool)     SetCollisionMode(short, int)    SetCollideDrag(char)
SetCollisionLogEib / SetCollisionLevelERKSt / SetCollideDragERKSt / SetCollideDragEc
SetLoad(...) / SetLoadParam(tagLoadParams*, int) / loadSet(_stLoadParams*, bool) / GetLoadParam()
SetSafeSkinCmd(short, bool) / SetSafeSkin(...) / SetDragSenseParams(DragSenseAdjust*, bool)
```

### 5.4 配置文件位置（两套路径，通常要同时改）

```
/dobot/userdata/CR5_sys_files/project/{properties,settings,logs}/
/dobot/userdata/project/{properties,settings}/
```
* `properties/AdvancedFunction.json` —— 阈值（`SteadyErrorThreshold` 等）
* `properties/alarm_servo.json` / `alarm_controller.json` —— 报警表
* `settings/function/collisionDect.json` —— 碰撞 5 档
* `settings/function/loadParams.json` —— 负载重量/重心
* `settings/function/homeEncoder.json` —— **标零记录（`innerEncoder` 只是日志，不参与运算）**
* `properties/slaveInfos`（Recipe 里）—— EtherCAT 从站清单
* **`logs/all/log`** —— 主日志（**判据都在这里**）

---

## 6. ★ 方法（怎么查、怎么判）

### 6.1 只读手段（优先级从高到低）

| 手段 | 做法 | 特点 |
|---|---|---|
| **HTTP SDO 读** | `POST :22000/settings/readServoParams` | **标准 CiA402 对象可读**（`0x6064`/`0x603F`/`0x607D`…）；**厂商参数 `0x20xx` 在 3.1.5.0 上读不到（全返 0）** ✗ |
| **内存直读（最安全）** | `tools/amrd <pid> <addr> <len> raw` ⇒ 读 `codesyscontrol` 的 `/proc/PID/mem` | 纯 `pread`，**不碰总线**；用来抓 TxPDO 输入映像 |
| **日志判据（最快）** | `grep -a 'PoseTrace\|logServoError\|AlarmSysSetBit\|HomeNumdone\|servo calihome' logs/all/log` | 几乎所有结论都能只靠日志得出 |
| SOEM 直读 | `tools/ecat_read`（静态 ARM） | **会和运行中的主站抢总线** ⇒ 非必要不用 |

### 6.2 日志里的关键行（判据）

```
PoseTrace: gRobotAxisMove.nextPos:      ← 主控规划值
PoseTrace: (PDO0x6062)Position demand:  ← 驱动器给定
PoseTrace: gActualPosition:             ← 主控读到的"实际"（**原版下=0x6062，补丁下=0x6064**）
logServoError#... servoN error ID update : A -> B     ← 驱动器故障码变化
[updateEncoderData#507] HomeNumdone : N  /  #509 servo calihome done ...   ← 标零进度
[monitorServoUptime#527/534] robot enabled/disabled, this enable last N sec ← 使能时长（0~2 秒=异常）
[readSDO#4613/4624] sdo read/fail,slave=N,index=...,value=...              ← SDO 真值在这
[InitScaraParams] st_advanced_function : SteadyErrorThreshold:...          ← 实际加载的阈值
```

### 6.3 ★ 每次改完必须做的三步验证

1. **看日志确认生效**（`[InitScaraParams]` / `servo calihome done` / `PoseTrace` 三列）
2. **看 `gActual` 是否合理**（六轴 ≈0 ⇒ 零点有效）
3. **看是否有**新**报警**（`AlarmSysSetBit` 的最新几行）

---

## 7. 工具与文件清单（都在本目录）

| 文件 | 用途 |
|---|---|
| **`test.py`** | ★ 十点十段运动测试 GUI：每段前做**台面+地面碰撞预检**（`SolveIK_All` 枚举换解），P4/P8 为**奇异点**（跳过 IK，仅 J6 ±180°） |
| `COLLISION_AVOIDANCE_PLAN.md` | ★ 碰撞误报的五层方案 |
| `SERVO_PROTECTION_FINDING.md` | 保护报警码表 + 判据参数 |
| `tools/rssh.py` | **SSH 通道**（paramiko）：`-f 脚本.sh` / `--put` / `--get` / `"命令"` |
| `tools/amrd` / `amscan` | 控制器侧静态 ARM 内存工具（只 `pread`） |
| `tools/read_protect_params.py` | 逐轴读保护参数 |
| `tools/lookup_servo_alarm.py` | 按码查伺服报警 |
| `tools/servo_protect_family.py` | 列出保护族 + 查参数表 |
| `tools/check_test_py10.py` | 校验 `test.py` 十段结构 |
| `tools/check_format_runtime2.py` | **运行时**校验脚本里所有格式串（能揪出 `%` 占位符错位） |
| `data/` | 报警表/配置快照（离线可查） |

---

## 8. ⚠️ 踩过的坑（**红线**，别再犯）

### 8.1 工具/命令类

1. **⛔ 绝不用 PowerShell 内联写含引号/`$()`/中文的命令给 SSH** —— 一定被吃掉或语义改变（本会话踩了 **6 次以上**）
   ⇒ **一律写脚本文件，用 `tools/rssh.py -f <file.sh>`**
2. **⛔ 不用内联 `python -c` 写文件**（曾把一个 10 KB 脚本截成 0 字节）⇒ 用 `write`/`edit` 工具
3. **⛔ 不用 PowerShell 改含中文的文件**（会破坏编码）⇒ 用 `write`/`edit`
4. **⛔ `grep -rl` 不要扫 `/dobot/userdata` 全目录**（会把 GBK 大日志卷进来，输出爆炸）⇒ 缩窄路径
5. **⚠️ `%` 格式化必须核对占位符数** —— 本会话写 GUI 文本时 15 个占位符配 14 个参数 ⇒ `TypeError`
   ⇒ **长文本一律用 `+` 字符串拼接**（`tools/check_format_runtime2.py` 可自动查）

### 8.2 RoboDK/机器人 API 类

6. **⛔ `robot.Joints()` 在 `RUNMODE_RUN_ROBOT` 下不可用**（返回 1×1 `[[0]]`）⇒ 用 **`robot.SimulatorJoints()`**
7. **⛔ `MoveJ_Test` / 障碍物预检只能在 `RUNMODE_SIMULATE` 下做** ⇒ 用完**必须切回 `RUNMODE_RUN_ROBOT`**
8. **⛔ `SolveIK` / `SolveIK_All` 要的是【法兰】位姿**，不是 TCP 位姿
   ⇒ `robot.PoseFrame() * pose * invH(robot.PoseTool())`（漏了这一步会解不出逆解）
9. **⛔ 碰撞预检不能"用单一 IK 解去测、撞了就拒绝"** —— 那不叫检测，叫拒绝任务
   ⇒ 必须 **`SolveIK_All` 枚举 → 排序（肘部离台面高者优先）→ 逐个 `MoveJ_Test` → 取第一个通过的**
   ⇒ 并且**要用选中的那个构型去执行**（否则"检查过的解 ≠ 走的解"）
10. **⚠️ `StoppedError: Robot not connected` 是**假报警**（指令已发出，报错在"等待完成"阶段）**
    ⇒ 用 `SimulatorJoints()` 判断"动过 + 停稳"，不要重发

### 8.3 结论类

11. **⛔ 跨版本比较别用间接指标**（计数/普查）—— 本会话历史上有 **4 次**因此得出错结论
    ⇒ "某版有/没有 X" 必须**逐条读码**或**实测**
12. **⚠️ 写 `SavePos.txt` 没用** —— 主控**每次开机**都会用它读到的实际值覆盖它
13. **⚠️ `homeEncoder.json` 的 `innerEncoder` 只是记录**，改它不生效（已实测）

---

## 9. 待办与建议（按推荐顺序）

| 优先 | 事项 | 做法 | 风险 |
|---|---|---|---|
| **1** | **修正负载参数**（疑为碰撞误报根因） | 示教器设工具重量/重心，或 `SetLoad(weight,cx,cy,cz)`；现为 0.2 kg ✗ | 无 ✓ |
| **2** | **验证零点持久性** | 整柜断电 ≥30 s → 上电 → 读六轴应仍 ≈0（3.1.5.0 的老毛病是"不保持"） | 无 ✓ |
| **3** | **碰撞等级 2 → 1** | 改 `collisionDect.json` 的 `"level"`（两套路径）→ 重启 | 低 ✓（保留大幅碰撞保护） |
| **4** | **研究"碰撞后行为"** | 先在 DobotStudio 里找界面（背后是 `SetCollisionMode`/`SetCollideDrag`）；或让我离线逆向取值域 | 中 |
| **5** | **`unio` 板掉线 `0x82`** | 先查柜内该板的**网线/插头/供电**；无效则用 **`CR_UniIO_ST_FOE_V2.3.4.1.bin`**（在 `D:\software\dobot\V1.3.4-stable\upgradeFiles\3.5.6\3.5.6.1\files\`）重刷 | 中 |
| **6** | **`H01.17` = 0 的 A/B** | 用维护工具把 J2 的 `H01.17` 写回 330，观察 `0x6064` 是否变化 | 中（改驱动器参数） |
| **7** | **拍板 `0x8612` 判据** | 维护工具里读 `H0B.13`（触发次数）；若 >0 则把 `H0B.12` 由 3 改 7 | 中 |

### 建议的第一件事

```bash
# 只读确认机器现状（见 §3），然后按上表第 1 项动手（零风险）
```

---

## 10. 一页纸总结（给 GLM 的最小上下文）

* **要解决什么**：3.1.5.0 伺服下，让 CR5 的零点有效、能按十点轨迹稳定运动、并让"末端作业中的硬接触"不误报停机。
* **已经解决**：零点（标零走完 0→2→4→6，六轴 ≈0）；"J2 显示 365°"（查明是主控侧多一圈）；稳态误差误报（阈值 →1.0）；SDO 只读通道；`test.py` 十段运动 + 碰撞预检换解。
* **关键知识**：标零**必须**在原版主控下做；`SolveIK*` 要法兰位姿；碰撞预检必须**枚举换解**；命令口**单客户端**别乱探。
* **未决**：`unio` 掉线报警、`H01.17`=0、`0x607D` 默认限位、碰撞等级/负载/碰撞后行为。
* **红线**：不要关碰撞检测总开关；不要用 PowerShell 内联复杂命令。
