# LINUX_CHAIN_FINDING.md — `/calibrate/home` 的完整链路 + 一条全新的**现场 SDO 探针**

> 第 36 轮（2026-09-24 15:40–15:50，控制箱在线）。**本轮未动机器人、未碰总线、未改任何文件**；
> 对控制箱只做了两件事：读日志、发 HTTP **只读** SDO 请求。
> 工具：`tools/gcontrol_dig.py`、`tools/libdata_plt.py`、`tools/libdata_xref.py`、
> `tools/libdata_strrefs.py`、`tools/libdata_routes.py`、`tools/libdata_callers3.py`（作废，见 §7）。
> 原始留档：`data/cabinet/CONN_REQ_DIR.txt`、`DATASUBPROC_CTOR.txt`、`SETSERVOPARAMS.txt`、
> `SERVOPARAMS_ROUTES.txt`、`CHECKREQLOOP.txt`、`SDO_PROBE_LOG.txt`、`SDO_PROBE_LOG2.txt`、
> `SDO_VENDOR_PROBE.txt`、`SDO_REPEAT.txt`、`SDO_PDO_READBACK.txt`、`SDO_SWEEP_J6.txt`、`CTRL_NET_PS.txt`。

---

## 0. 一句话结论

1. ⛔ **`/calibrate/home` 不是 gcontrol 提供的**。端口 **22000 属于 `codesyscontrol`**（pid 375），
   `libdataSvr.so` / `libalgs_framework.so` 都由它加载；**gcontrol 里连 "calibrate" 这个字符串都没有**。
   ⇒ 上一轮"拉 gcontrol → 找路由表"的计划基于错前提，**已作废**。
2. ✅ **`libdataSvr.so` 的 PLT 已 100% 解出（2932/2933）**，从此**库里每一条调用都能叫出名字**。
   这也解释了卡了两轮的怪事：**同库内默认可见性符号的调用走 PLT 桩**（`blx 0x000b....`），
   所以"扫 `bl <函数地址>`"必然返回 0 —— **不是没有调用者，是工具结构性看不见**。
3. ★★ **主控里有一条 HTTP 的 SDO 读写通道**（`/settings/readServoParams`、`/settings/modifyServoParams`），
   本轮把它**跑通并做成了只读探针**。
4. ★★★ **探针结果推翻了"主控报的关节角 = 驱动器 `0x6064`"这个一直以来的前提**：
   对 J1–J5（3.2.D.8）两者**完全相符**（只差符号/方向），对 **J6（3.1.5.0）完全不相符**。
   这是迄今**最锐利**的一条新线索，见 §5、§6。

---

## 1. 修正的旧假设（本轮推翻/更正）

| # | 旧说法 | 现状 | 依据 |
|---|---|---|---|
| 1 | 路由表在 gcontrol 里 | ⛔ **作废**。gcontrol 全文无 "calibrate"；22000 端口属 codesyscontrol | `netstat` + 全文串搜（`gcontrol_dig.py`）|
| 2 | `caliHome` 在 `libdataSvr.so` 里没有调用者 | ⛔ **表述错误**。它是 HTTP handler，**由构造函数注册进路由表**，从不被"调用" | §3、§4 |
| 3 | 三次"找不到调用者"的扫描 = 正确弃权 | ⚠️ **弃权是对的，但结论是被误读的**。当时扫的是 `bl <绝对地址>`，而库里跨目标文件的调用走 **PLT 桩** | §2.2 |
| 4 | `sdo write fail,...` 说明 SDO 写失败 | ⛔ **字符串误导**：`readSDO`/`writeSDO` 的日志是**成功路径上无条件打印**的，
  真正的成败在结构体另一字段（`[runtime+0x4dc]` 是否 ==1）。**别用日志串判断成败** | §4.4 + §5 旁证 |
| 5 | 厂商对象 SDO 写不进去 ⇒ SDO 通道整体不可用 | ⛔ **SDO 通道可用**，标准对象与厂商对象都能读回真实值 | §5 |
| 6 | `libdata_annot2.py` 的 PIC 串解析正确 | ⛔ **有 bug**：该工具链用 **`insn.address+4`（不做 4 字节对齐）** 算 PC；
  对齐版本会让 `add rX,pc` 落在 `addr%4==2` 的站点**整体偏 2 字节** | §2.3 |

---

## 2. 工具链

### 2.1 `tools/libdata_plt.py` —— PLT 数据驱动解析器（**必须的工具**）
不假定 PLT 头长度与桩顺序，而是逐个候选起始点解码经典 ARM 桩：
```
add  ip, pc, #imm1        ; 0xE28FC000|imm12   ← imm 是**旋转立即数**
add  ip, ip, #imm2        ; 0xE28CC000|imm12   ← 同上
ldr  pc, [ip, #imm3]!     ; 0xE5BCF000|imm12   ← **普通 12 位偏移，不旋转**
```
`slot = ((addr+8) + dp_imm(imm1)) + dp_imm(imm2) + (imm3)`；`slot` 命中 `.rel.plt` 的 `r_offset` 才收下。
**自检：覆盖 2932/2933 = 100.0%**（不达 90% 直接弃权）。
⚠️ 三个坑：① `ldr` 的偏移**不旋转**；② `add` 的立即数**要旋转**；③ 桩起始不是 `.plt` 偏移 0（头 0x14）。

### 2.2 `tools/libdata_xref.py` —— 带 PLT 名字的调用者查找
`find <符号>` / `dis <符号>` / `region <addr> <size>`。
**正例对照**：`robot_control::updateEncoderData` → `DataSubProcess::updateEncoderData`
找到 **2 处**（`0x001d9f80`、`0x001d9fa6`），与日志 `updateEncoderData#489/#15707` 完全一致 ⇒ 工具可信。
在此可信工具下：**`caliHome` 没有任何 PLT 桩，也没有任何直接调用** ⇒ 它**只被当作函数指针注册**。

### 2.3 `tools/libdata_strrefs.py` —— PIC 串引用扫描（**修掉一个真 bug**）
旧工具（含 `libdata_annot2.py`）用 `((addr+4)&~3) + offset`。实测该工具链用 **`(addr+4) + offset`（不对齐）**。
判据（可复现）：`'calibrate'` 的引用在 `0x0010c526`（`addr%4==2`），
**对齐版解析出 `0x00211b4e`（差 2，指向填充 NUL）⇒ 于是"calibrate 无人引用"这个假象持续了两轮**；
不对齐版得到 `0x00211b50` = `"calibrate"` ✅。
修后**路由 token 全部有引用**（`panel/settings/calibrate/process/properties/test/state/…`）。
**正例对照**：`"isRequestCalihome true"@0x00235324` 必须命中 `0x001db3e4`（对齐/不对齐都命中）—— 通过。
⚠️ **`libdata_annot2.py` 仍是旧算法**，读它的输出时凡 `addr%4==2` 的 `add rX,pc` 都要 **+2** 修正（或改用本工具）。

### 2.4 `tools/libdata_routes.py` —— 路由表重建（**半成品**）
思路对（uri 串 + GOT 槽 → 重定位 → 符号），但**配对会错位一行**（见 §3 注），
本轮的结论不依赖它，改由**日志里的真实 uri** 与**构造函数里的注册点**互证。

---

## 3. HTTP 路由表的真身

* 分发器：`DataSubProcess::conn_req_dir(evhttp_request*, void*)` @ `0x001002c4`（2560 B）。
  它把 URI 按 `/` 切成 **type/uri** 两段，查一张
  **`QHash< QString, QHash< QString, void(*)(evhttp_request*,void*) > >`**，
  该 Map 是 `DataSubProcess` 的成员，位于 **`this + 0x10CC`**。
  （类型名由 PLT 解出：`_ZNK5QHashI7QStringPS_IS0_PFiP14evhttp_requestPvEEE8findNodeERKS0_Pj`。）
  找不到时打 `"Can't find method type:{}"` / `"Can't find method:{} by type:{}"`。
* 注册者：**`DataSubProcess::DataSubProcess(int, QString)`（构造函数）** @ `0x0010b3f0`（**12,096 B / 4,202 条指令**）。
  注册块集中在 `0x0010c4b0 … 0x0010d838`；每条约 0x4e~0x50 字节：
  ```
  ldr r0,[pc,#a] ; add r0,pc          → &"<token>"（.rodata）
  mov r1,#-1 ; blx QString::fromAscii_helper
  ... QHash<QString, handler>::operator[] ...
  ldr r3,[pc,#b] ; ldr r3,[r6,r3]      ; r6 = GOT 基址 = 0x00269920（构造函数序言已证）
  str r3,[r0]                          ; 存入 handler 函数指针
  ```
* 由此**直接读到**（`PIC ->` 解析，token 顺序与 `.rodata` 池顺序一致）：
  `panel, settings, [calibrate], process, [properties], test, [state], getSuspend, stepIn, [stepOver],
  [setb], delb, [delallb], globalVar, threeSwitch, [emergencyStop], [exchange], [common],
  modifyServoParams, [readServoParams], teach, [playback], [version], autoIdentify, …,
  projRun, [home], coordinateSingle, leftRightHand, multiCalibration, …,
  goHome, [powerControl], … readCurrentEncoder …`
  （`[]` 内的 token 由**第二次串加载**给出，annot2 的 2 字节偏差让它们显示成邻串，见 §2.3。）
  ⇒ **`/calibrate/home` 的 handler 就是 `DataSubProcess::caliHome`**；`/settings/readServoParams`、
  `/settings/modifyServoParams` 在 `settings` 这一型下。
* ⚠️ 这一节属 **【逐条读码】** 级：注册点、GOT 基址、Map 成员偏移都是读出来的；
  **但"某个 token 归到哪一型"是靠池顺序 + 通配推断的**，要精确到 (type,uri) 对，
  需要把 §2.4 的配对修对（未做）。

---

## 4. ★ 主控侧的 SDO 读写通道（本轮最大发现）

### 4.1 符号（`libdataSvr.so`，全部有名字）
| 符号 | 地址 | 大小 |
|---|---|---|
| `DataSubProcess::readServoParams(evhttp_request*,void*)` | `0x000f9cdc` | 652 B |
| `DataSubProcess::modifyServoParams(evhttp_request*,void*)` | `0x0011a1ac` | 1016 B |
| `DataSubProcess::parseAndReqGetServoParams(...)` | `0x000ec03c` | 1080 B |
| `DataSubProcess::parseAndReqSetServoParams(...)` | `0x000ebaf4` | 1352 B |
| `DataSubProcess::readSDO(_SDOInfo&, int)` | `0x000eba0c` | 232 B |
| `DataSubProcess::writeSDO(_SDOInfo)` | `0x000eb974` | 152 B |
| `DataSubProcess::readSDOthd` / `writeSDOthd` / `createSDORWThd` / `exitSDOWRThd` | `0x000ec968` / `0x000eca0c` / `0x000f9c2c` / `0x000ec918` | |
| `DataSubProcess::getAndPackServoParams(std::string&)` | `0x000ec474` | 1188 B |

### 4.2 请求格式（**已实测可用**）
```
POST  http://192.168.5.1:22000/settings/readServoParams     (只读)
POST  http://192.168.5.1:22000/settings/modifyServoParams   (写；会落盘! 见 4.3)
Content-Type: application/json
体：
{ "body": [ { "key": "addr<索引4位HEX><子索引2位HEX>", "servoNum": "J1".."J6", "value": <n> } ] }
```
* key 例：`addr200C01` → 0x200C:01；`addr607C00` → 0x607C:00；`addr606400` → 0x6064:00。**已实测键格式正确**
  （日志里 `index=` 十进制与键逐项对上：`addr606400`→`24676`=0x6064 ✅）。
* `servoNum` 取 `"J1".."J6"`（代码里的表：`J1/J2/J3/J4?/J5?/J6`，`servoNum` 为键名）。
* 返回 **恒为 `{"status":true}`**（只表示 handler 接受了），**真实结果只在日志里**。
* **一次只允许一个请求在飞**：并发时后续请求返回 **HTTP 400**（`conn_req_dir#11537 ret_code!= HTTP_OK!!!, retcode = 400`）。
  ⇒ 探针必须**串行 + 间隔 ≥1 s**（本轮用 1.05 s）。

### 4.3 副作用（**重要红线**）
* `modifyServoParams` 会先把 body **写进文件**
  `/dobot/userdata/project/settings/function/servoParams.json`，再由线程读该文件下发。
  ⇒ **任何"写"请求都会在控制箱上留痕**（现场文件里现在留着 9/23 18:27 那次 `addr200C01` 的残留）。
* `readServoParams` 直接解析 POST body，**不落盘**。

### 4.4 为什么日志串会骗人（读码）
`readSDO` 尾部：`state=[runtime+0x4c4]`；**只有 state==3 才走到日志那条路**；
它把 `value=[runtime+0x4d4]` 存进结果，把 `success=([runtime+0x4dc]==1)` 存进结果+0x14，
**然后无条件打印 `"sdo read fail,slave={},index={},subIndex={},value={}."`**。
⇒ 日志串里的 `value=` **就是读回的值**；串里的 "fail" 是**厂商的文案 bug**。
（旁证：读回的是一堆有物理意义、且会 ±1 抖动的值，见 §5。）

---

## 5. ★★ 现场探针结果（2026-09-24 15:42–15:49，只读）

### 5.1 六轴 `0x6064`（位置实际值）与主控上报关节值（同一时刻）
| 轴 | 从站 | 从站固件 | 驱动器 `0x6064`（SDO 低 16 位，见 5.3） | 主控 30005 上报 | 主控折算计数 |
|---|---|---|---|---|---|
| J1 | 1003 | 3.2.D.8 | `63037` = **−2499** | +0.445389° | **+2499.1** |
| J2 | 1004 | 3.2.D.8 | `330` = **+330** | −0.058815° | **−330.0** |
| J3 | 1005 | 3.2.D.8 | `62983` = **−2553** | −0.455013° | **−2553.1** |
| J4 | 1006 | 3.2.D.8 | `2542` = **+2542** | −0.453052° | **−2542.1** |
| J5 | 1007 | 3.2.D.8 | `2499` = **+2499** | −0.445389° | **−2499.1** |
| **J6** | **1008** | **3.1.5.0（含我方补丁）** | **`65515` = −21** | **+20.504629°** | **+115053.8** |

* 计数换算用文档里的 `360/(20000×101) = 1.782178e-4 °/count`。
* **J1–J5：|驱动器 `0x6064`| == |主控折算计数|**（差 ≤0.1 计数，符号随机械方向）⇒ **两者同源**。
* **J6：−21 vs +115054** ⇒ **两者不同源**。⚠️ 且 `−21` 与 `+115054` 之差 115075 **不是 65536 的整数倍**，
  ⇒ **不能用"低 16 位截断"解释**（见 5.3 已证明截断存在）。
* 旁证：J6 的 `0x6064` 在 5 次连读中在 `65515/65516` 之间抖 ±1 ⇒ **这条读数是活的**；
  而主控的 J6 值在 45 分钟内**逐位不变**（`20.504629`）。

### 5.2 其它对象（J6，同为只读）
| 对象 | 读回 | 解读 |
|---|---|---|
| `0x6041` statusword | `38455` = `0x9637` | 低半字节 `0111` ⇒ **Operation enabled**，bit3(fault)=0 |
| `0x603F` error code | `0` | 无故障 |
| `0x6060` modes of operation | `8` | **CSP**（与文档假设一致）|
| `0x6061` modes display | `8` | 同上 |
| `0x6098` homing method | `35` | **35**（与文档假设一致），J1 也 = 35 |
| `0x6063` 位置实际值(内部) | `65515` = −21 | 与 `0x6064` 一致 |
| `0x607C` **Home offset** | **`0`**（J1 也是 `0`） | ⇒ **零点不在 Home offset 里** |
| `0x606C` 速度实际值 | `0` | 静止 |
| `0x606B` 速度指令 | `0` | 静止 |
| `0x6077` 转矩实际值 / `0x6078` 电流实际值 | `21` / `21` | |
| `0x6075` / `0x6076` | `2800` / `300` | 电机额定电流/转矩 |
| `0x6079` 母线电压 | `47` | ⚠️ 偏小，疑与 5.3 的截断/量纲有关 |
| `0x5000:01` / `:02` / `:03` / `:06` / `:07` / `:08` | `31` / `1` / `1` / `61` / `12624` / `60025`(=−2511) | 厂商状态对象，**SDO 能读到真值** |
| `0x5001:06` / `:07` / `:10` | **`0` / `0` / `0`** | ⚠️ 见 §6.3 |
| `0x5002:03` / `:04` / `:06` | `0` / `0` / `0` | |

### 5.3 ✅ 已证明：**32 位对象只回低 16 位**
读 `0x1A00`（TxPDO 映射）逐子索引：
`sub0 = 24`（J6）/ `20`（J1），`sub1 = 16`，`sub2 = 8`，`sub3 = 32`，`sub11 = 272`，`sub12 = 528`，…
对照主控启动日志里它写下去的值：`1A00.3 = 16#60640020`、`1A00.11 = 16#50000110`、`1A00.12 = 16#50000210`。
`0x60640020 & 0xFFFF = 0x0020 = 32` ✅；`0x50000110 & 0xFFFF = 0x0110 = 272` ✅。
⇒ **读回值 = 该对象的低 16 位**（截断已被实证）。
⇒ ★ **同时这也证明：驱动器接受的 TxPDO 映射与主控写下去的完全一致**（J6 与 J1 都是），
所以"映射没被接受"这个解释**被排除**。

### 5.4 探针的可复现命令
```bash
# 在控制箱上（或从 192.168.5.x 直连 22000）
wget -q -O - --header='Content-Type: application/json' \
  --post-data='{"body":[{"key":"addr606400","servoNum":"J6","value":0}]}' \
  http://127.0.0.1:22000/settings/readServoParams
# 结果去日志里看：
grep -a 'readSDO#46' /dobot/userdata/CR5_sys_files/project/logs/all/log | tail
```
（本机用 `urllib` 直连 `192.168.5.1:22000` 亦可；控制箱上**没有 curl，只有 wget**。）

---

## 6. 推论

### 6.1 已被证据支持的
1. **主控侧不存在任何"把零点写进驱动器"的命令**：`caliHome` 只是把已算好的 6+6 个 double
   从 `*(this+0xE20)+0x3110/+0x3278` 拷进 `this+0x20C0/+0x20F0`，置 `isRequestCalihome`；
   真正动作由 `checkRequestLoop` 上报给下层（PLC）。**与总线抓包的结论一致**（只写 RxPDO `0x607A=0`）。
2. **`0x607C Home offset` 两版都是 0** ⇒ "驱动把零点写进 Home offset"这条假设**出局**。
3. **`0x6098 = 35`（homing method 已设为 35）、`0x6060 = 8`（CSP）** —— 与 §TASK_STATE 的推测吻合，
   但**驱动器里没有 CiA402 Profile Homing 状态机**（`SERVO_SUMMARY.md` §12 的决定性否定 ① 仍成立）。
4. **SDO 通道本身是好的**，标准与厂商对象都能读；"厂商对象写不进去"这个旧结论**至少对读不成立**（写未复测）。

### 6.2 ★ 新的头号线索（**未证，但可判**）
> **对 J6，主控上报的关节角不是驱动器 `0x6064`。**

给出三个可能（按可能性排序）：
1. **J6 的 TxPDO 槽位里放的不是 OD 的 `0x6064`**：驱动器 `1A00` 的映射回读与主控写的一致（§5.3），
   但**回读只能看到低 16 位（长度字段），看不到索引**（`0x6064` 高半字被截掉）。
   ⇒ 3.1.5.0 的固件**可能把"原始绝对计数"喂进了 `0x6064` 那个映射项**。
   ⚠️ 这是 3.1.5.0 与 3.2.D.8 在**过程数据层**的差异，与"OD 访问层两版逐项相同"并不矛盾。
2. **主控对 J6 用了另一条通路的对象**：J6 的 TxPDO 映射比 J1 多 4 项，
   其中 **`0x5001:06 / :07 / :10`（各 32 位）在 J1 上根本不存在**（J1 的 `1A00` 只有 20 项，J6 有 24 项）。
   而 `0x5001:06/07/10` 经 SDO **读回全 0**（PDO-only 对象 SDO 伺服可能不实现）
   ⇒ **它们里面装 32 位原始计数是完全可能的**，且数值 115054 正好是"多圈绝对计数"的量级。
3. 主控侧值被**冻结**（PLC 变量没刷新）。可能性最低：J1–J5 的读数在 45 min 内也几乎不动，
   但它们的驱动器读数也没动，无法区分；且 9/23 的 A/B 测试里 J6 的值确实会在上/下使能时跳变。

### 6.3 三种可能的判别实验（都不需要碰总线）
1. **（首选，离线+在线混合）扫描 `codesyscontrol` 进程里的 TxPDO 输入映像**：
   在 `/proc/375/mem` 里搜 32 位数 `0x0001C16E`（=115054）与 `0xFFFFF63D`（=−2499），
   找到它们的**字节位置**，对照 §5.3 的映射表算出"它落在第几个映射项"，
   即可**直接指认**主控到底读的是 `0x6064` 还是 `0x5001:06`。
   工具现成：`tools/amrd.c` / `amscan.c`（只 `pread`，**不碰总线**）。
2. **读 `0x1A00` 的高半字**：SDO 只回低 16 位 ⇒ 做不到，除非改用别的通道。
3. **现场微实验（需用户点头）**：只做一次 **下使能 → 上使能**，同时
   在日志侧连读 J6 的 `0x6064`、在主控侧读 30005。
   * 若驱动器 `0x6064` 一直 ≈0 而主控值在改变 ⇒ **两者不同源**，嫌疑指向 1/2，且**J6 的零点其实是保住的**；
   * 若驱动器 `0x6064` 跟着弹回 115054 ⇒ 是驱动器的定基没保住（旧结论成立）。
   ⚠️ 该实验会让机械臂动作一下（历史上幅度只有零点几度），**必须先征得用户同意**。

### 6.4 若 6.2 的第 1/2 支成立，意味着什么
那么"零点不保持"的**真实机理**是：
**驱动器内部其实定基了（`0x6064`≈0），但主控从 PDO 里拿到的仍是原始绝对计数**；
3.2.D.8 之所以"正常"，是因为那一版**把定基后的值送进了 PDO**。
⇒ 修法就从"让驱动器接受定基"变成"**让主控读到定基后的值**"——
后者**完全在 Linux 侧**，可以不改固件（例如主控侧消差，或改 J6 的 TxPDO 映射让它去读别的对象）。
⚠️ **但这与 §TASK_STATE / 总线抓包的旧观测冲突**（旧观测：3.1.5.0 的 PDO `0x6064` **纹丝不动**、
且"重新上使能弹回 45877"），**所以必须先做 6.3 的判别实验，不能直接采信**。

---

## 7. 本轮作废/降级的东西

* ⛔ `tools/libdata_callers3.py`：控制逻辑没错（`bl` 目标 192/192 落在符号起点，控制 PASS），
  但**它只能看直接 `bl`**，对这个库**没用**（真正的跨文件调用走 PLT）。
  已在 `data/cabinet/CONN_REQ_DIR.txt` 里留档其输出，**不要再用它的"0 callers"下结论**。
* ⛔ `tools/libdata_routes.py`：handler 配对会错位一行，**仅作参考**。
* ⛔ "gcontrol 里有路由表" —— 作废。
* ⚠️ "整文件搜某个代码地址的 dword" —— 又一次踩到 **`.symtab` 自命中**假阳性
  （`0x000f0428` 命中 `0x270518`，落在 `.symtab` 的 `st_value` 字段）。
  **`libdataSvr.so` 是 PIC 共享库，数据段里不存代码绝对地址** ⇒ 这条路永久关闭。
* ⚠️ **红线（新增）**：**不要用厂商日志串判断 SDO 成败**；也不要用"并发 400"判断服务坏了
  （那是设计上的一次一请求锁）。
