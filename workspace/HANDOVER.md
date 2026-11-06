# HANDOVER —— 2026-09-23 会话交接（零点写入 / CODESYS PLC 逆向）

> ⚠️ **本文件之后又开了一轮会话，见 `HANDOVER_2.md`**（`.app` 映射表 + 伺服固件逆向）。
> 读完本文件请接着读 `HANDOVER_2.md`，那里有本文件 §6「B 计划」的完成情况与新的现场状态。
> （本文件保留为**第一轮**的记录，其中"控制箱在线"等现场描述可能已过期。）

> 本文件是 **新开会话的第一份阅读材料**。读它 + `AGENTS.md` + `FINDINGS.md` 就能接上下文，
> 不需要重读旧对话。旧会话上下文已耗尽，这里是全部关键状态的显式落盘。

---

## 0. 一句话现状

**目标**：在伺服固件 **3.1.5.0** 上让 J6 的零点能保持住（用户明确否定了"刷 3.2.D.8"，因为它无法满足机械臂的**运动**要求）。

**结论**：零点住在**驱动器厂商私有参数空间**（H 参数），唯一的门是 **CODESYS PLC 的原生轴参数通道**，
而旧通道（libdataSvr → CODESYS 共享内存邮箱）**结构性损坏、本机历史上从未成功过一次**。

**⚠️ 未解决的现场问题**：J6 读数 **20.5°**（物理位置未动，用户已确认），原因未明，**别发运动指令**。

**✅ 本轮进展（2026-09-23 19:3x）**：`Application.app` 的**文件偏移 ↔ 运行时地址映射已建立**（660 段 / 9 个 Δ 池 + 换算器），
见 **`APP_OFFSET_MAP.md`** 与 `data/appmap/`。B 计划还差**导入 Ghidra** 这最后一跳。

---

## 1. 设备与访问（不变）

| 项 | 值 |
|---|---|
| 控制器 | `192.168.5.1`，SSH root（`rrun.cmd` / `rscp.cmd` + `.askpass.cmd`，工作区根目录） |
| 远端 shell | BusyBox ash（**没有 bash**；grep/awk 是精简版：**无 `-b`、无 `strtonum`**） |
| 本机 | `192.168.5.2`（eth2 机器人网）；**EtherCAT 在 eth0** |
| 控制器进程 | `codesyscontrol`（**libdataSvr.so 就加载在它里面**，HTTP 22000 也是它） |
| 伺服从站 | slave **3=J1, 4=J2, 5=J3, 6=J4, 7=J5, 8=J6**（总线上共 9 个从站） |
| 伺服固件 | J1–J5 = `3.2.D.8`（零点正常），**J6 = `3.1.5.0`（零点丢失）** |

---

## 2. ✅ 已破解、可直接复用的东西

### 2.1 伺服参数 HTTP 写通道（**本机历史首次跑通**）

**必需的"门禁文件"**（不存在则走另一分支）：
```
/dobot/userdata/project/settings/function/servoParams.json
```
**内容格式**（与读路径同构）：
```json
{"body":[{"key":"addr200C01","servoNum":"J6","value":0}]}
```
**触发请求**（**必需的成员是 `src`**，取值只有两个）：
```
POST /settings/modifyServoParams
{"src":"files"}        ← 从上面的文件读参数（IsWriteFromFile=true）
{"src":"httpClient"}   ← 从请求体读参数
```
其他键名一律 **400**。`value` 是必需的。

**地址编码（实测证实）**：
```
addr + hex(0x2000 + H组号) + 两位十进制(组内序号+1)
H0C.00  →  addr200C01  →  index=8204(0x200C), subIndex=1
H01.17  →  addr200118  →  0x2001:18
```
**应答的日志铁证**：
```
writeSDOthd#4902] writeSDOthd.IsWriteFromFile=true.
parseAndReqSetServoParams SDOWRCount = 1
parseAndReqSetServoParams#4668] start write sdo tp codesys.
writeSDO#4595] sdo write,slave=8,index=8204,subIndex=1,value=0.
parseAndReqSetServoParams#4676] sdo write fail,slave=8,index=8204,subIndex=1,value=0.   ← 250ms 超时
```

### 2.2 ⛔ 但它最终失败 —— 根因已定

- `readSDO`/`writeSDO` 都是**往共享内存邮箱写请求**（`*(this+0xe20)` 的 `+0x4c4` 状态 / `+0x4c8` 从站 / `+0x4cc` index / `+0x4d0` sub / `+0x4d4` 值 / `+0x4dc` 状态），然后等 250 ms
- **CODESYS 侧从不把状态置回 3** → 永远超时
- **全日志历史（52 万行）里该功能从未成功过一次**
- **重启后照样失败** ⇒ 结构性损坏，与运行状态无关
- 该邮箱**不在 codesyscontrol 映射的 7 个 SysV 段里** ⇒ 很可能是**进程内内存**，PLC 侧压根没轮询

### 2.3 ✅ 我们自己的可靠 CoE 通道

| 工具 | 位置 | 能力 |
|---|---|---|
| `ecat_zero` | 工作区根目录（静态 ARM） | `read` / `home <s>` / `rv <s> <idx> <sub>` / `wv <s> <idx> <sub> <v>` —— **100% 可靠** |
| `ecat_mbx.c/.exe` | 工作区根目录（Zig 交叉编译） | 原始帧邮箱 SDO：`rd/wr/scan/sregs/peek/poke/lrd/lwr/diag` |

**已验证能写**：`0x607C` 写入 −16425 → 回读一致 → 写回 0（闭环）
**H 参数写不了**：`0x2001:18` / `0x200C:1` / `0x2000:21` → **读 FAIL、写 wkc=0**（健康轴 J1 同样）⇒ **H 参数不是 CoE 对象**

### 2.4 ⚠️ 操作纪律（血泪教训）

**`ecat_zero` 和 `ecat_mbx` 都会破坏总线**：
- `ecat_zero` 的 `ec_config_init()` 把**全部从站强制切到 PREOP**
- `ecat_mbx` 翻转 SM1 Activate（`0x080E`）会**去激活 SyncManager**，同样踢从站出 OP

**后果**：CODESYS 报 `ETC device is no longer in mode operational`，机器人进报警、**上不了使能**。
**⇒ 规则：需要用总线工具 → 先下使能 → 做完 → 立刻重启控制器。** 且 `/tmp` 是 tmpfs，重启后工具要重传。

---

## 3. ⛔ 已封死的路（**不要重走**，附证据）

| 路 | 结论 | 证据 |
|---|---|---|
| HTTP 伺服参数通道 | ❌ 结构性死 | 见 §2.2 |
| H 参数经 CoE 读写 | ❌ 不是 CoE | J6/J1 全 FAIL，写 wkc=0 |
| `0x607C` + 断电重启 | ❌ 不可复现 | 写 −16425 后变 20.5°，写 19171 后**毫无变化** |
| `homeEncoder.json` 当偏置 | ❌ 纯日志 | 改 `innerEncoder[5]=115043` → J6 无变化 |
| CiA402 回零（`0x6060=6`+`0x6098=35`+cw bit4） | ❌ 执行不了 | 驱动器被主站占用时 `0x6060←6` **wkc=−5**，mode 显示恒为 8(CSP) |
| OPC-UA(4840) 写 PLC 变量 | ❌ 符号未发布 | 地址空间只有 `DeviceSet/SYSJ-CORTEX-Linux/Resources` 和 `Server` |
| `libCmpDobot6Axes.so` | ❌ 无关 | 纯运动学组件（`RobotCreate`/`RunRobot`/`RobotJoint`） |
| `0x1010`（参数保存） | ❌ 不存在 | 六轴全 FAIL |

---

## 4. 🔑 关键事实（新会话必须知道）

1. **关节角 = `0x6064` × `1.782178e-4`**（=360/(20000×101)）
2. **`innerEncoder`（homeEncoder.json）= 标定时刻的关节位置快照**（J1–J5 的值 × scale **逐位等于实测关节值**），**不是偏置**
3. **标定时控制器从 J6 读到的是 0**（15:55 与 18:40 两次记录 J6 都是 0，而 J1–J5 是真实值）
   ⇒ **3.1.5.0 的 `0x6064` 在下使能时归零**，上使能才加回一个陈旧的存储零点
   ⇒ **"标定"对 J6 等于没标**
4. **PLC 用的是 CODESYS 原生轴参数通道**，不是 libdataSvr 的邮箱：
   ```
   Device.Application.IoConfig_Globals.a1 … a6
     ├─ aN.config.read / aN.config.write     ← ★ 参数通道（目标）
     ├─ aN.read / aN.write                   ← 周期 PDO 数据
     └─ aN.DSP402_Statemachine.read/.write   ← CiA402 状态机
   Device.Application.DobotM1.{homeRobot,resetRobot,setmodeRobot}
   ```
   **这些名字在 `.app` 代码里是内联字符串字面量，通过运行时"按名字解析"服务访问**（`blx r0` + 名字压栈，六轴各一份）
5. **CODESYS 的 EtherCAT 驱动自己能成功发 SDO**（日志：`Cmp=IoDrvEtherCAT ... SDO write ok: Address: 1003 Index: 16#1A00 ... Result: 16#00`）⇒ 断点只在"libdataSvr→PLC"那一环
6. **⚠️ J6 读数 20.5° 原因未明**：物理未动，读数从 2.93° 变成 20.5°；`0x607C`/`homeEncoder.json` 均已排除。**但这证明存储零点可被外部改写** ⇒ 是条真线索

---

## 5. 工具链（已全部装好）

| 工具 | 路径 | 说明 |
|---|---|---|
| **Ghidra 12.1.4** | `D:\software\disassembly\ghidra\ghidra_12.1.4_PUBLIC\` | 项目目录 `D:\software\disassembly\ghproj\`（**libdataSvr.so 已分析完毕，7621 函数**） |
| **JDK 21 Temurin** | `D:\software\disassembly\jdk21\jdk-21.0.12.1+1\` | |
| Ghidra 脚本 | `D:\mydata\workspace\tools\ghidra\` | `list_funcs.java` / `decomp.java` |
| Zig 0.14.1 | `D:\mydata\workspace\.tools\zig\` | 交叉编译 ARM 静态二进制 |
| Python 库 | 系统 Python 3.14 | pefile / capstone / keystone / unicorn / lief / pyelftools |
| 二进制样本 | `D:\mydata\workspace\data\Application.app`、`libCmpDobot6Axes.so`、`libdataSvr.so.bin` | |
| **`.app` 运行时镜像转储** | `data\appmap\high_73000000.bin.gz`（64 MiB @ `0x73000000`，gzip 后 6.9 MB） | 地址 = `0x73000000` + 文件内偏移；应用镜像在 `0x75a76000-0x75cb8000` |
| **`.app` 映射表 / 换算器** | `data\appmap\app_map.json`、`tools\app_resolve.py` | `--to-runtime` / `--to-file` / `--coverage` / `--check` |
| **控制器侧内存工具** | `tools\amrd.c` / `amscan.c` / `amdump.c` → 静态 ARM | Zig：`zig cc -target arm-linux-musleabihf -Os -static`（缓存目录需设 `ZIG_GLOBAL_CACHE_DIR` 到工作区内） |

### Ghidra 使用配方

```powershell
$env:JAVA_HOME='D:\software\disassembly\jdk21\jdk-21.0.12.1+1'
$h='D:\software\disassembly\ghidra\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat'
# 首次导入+自动分析
& $h 'D:\software\disassembly\ghproj' dsh -import <文件>
# 之后秒级复用
& $h 'D:\software\disassembly\ghproj' dsh -process <程序名> -noanalysis `
     -scriptPath 'D:\mydata\workspace\tools\ghidra' -postScript <脚本>.java
```
**坑**：① 项目目录必须预先存在；② **Ghidra 12 的 Python 脚本需要 PyGhidra → 用 `.java` 脚本**。

**Ghidra 地址 = 0x10000 + 我们用的文件偏移**（已印证：`readSDO @0x0fba0c`、`parseAndReqGetServoParams @0x0fc03c`、`modifyServoParams @0x12a1ac`、PLT 桩步长 12）

> ⚠️ 这条只对 **ELF（`libdataSvr.so`）** 成立。**`.app` 不是 ELF**，它是归档 + 加载时重定位，
> 静态文件里的交叉引用全是占位值 ⇒ **`.app` 必须用运行时镜像分析**，偏移换算见 `APP_OFFSET_MAP.md`。

### 下载（国内）
**`https://gh-proxy.com/` + GitHub URL = 3–6 MB/s**（GitHub 直连失败；`ghfast.top`/`ghproxy.net` 仅 ~110 KB/s；developer.arm.com 仅 43 KB/s）

---

## 6. ▶️ 下一步计划（明确、已开工）

### B：解开 `Application.app` —— ✅ 映射表已交付（2026-09-23 19:3x，详见 `APP_OFFSET_MAP.md`）

**已判明**：`.app` **不是绝对地址镜像**，而是**归档 + 加载时重定位**（文件里是低位占位值，运行时是真实地址）。
本次量化：占位 dword 共 231,073 个；**载荷被抽取**（每条记录丢 20/23/27/31 字节的头），
运行时镜像比文件**小约 3.3%** ⇒ **映射必须分段，单一基址无解**（这正是原计划第 1 步"base 分组"的准确形态）。

**交付**：

| 产出 | 位置 |
|---|---|
| 映射表（**660 段 / 9 个 Δ 池**） | `data/appmap/app_map.json` |
| 换算器（双向 + 自检 + 覆盖率） | `tools/app_resolve.py` |
| 重建脚本 / 字符串锚点 | `tools/app_map_table.py`、`tools/app_strings_map.py` |
| 内存转储（64 MiB @ 0x73000000+） | `data/appmap/high_73000000.bin.gz` |
| 控制器侧转储/检索工具（静态 ARM，Zig 编译） | `tools/amrd.c`、`tools/amscan.c`、`tools/amdump.c` |
| 结论文档 | **`APP_OFFSET_MAP.md`** |

**核心数字**：镜像在 **`0x75a76000-0x75cb8000`**（maps 里那段被标成 `[stack:383]` 的 2.3 MB 匿名 `rwxp`，**不是栈**）；
主 Δ = **`0x75a95cd0`**（`runtime = file_off + Δ`，池内恒定、跨池跳变，**重启前后一致 ⇒ 可缓存**）；
`Device.Application.IoConfig_Globals.a1.config.write` 文件 `0x0e9f08` ⇒ 运行时 **`0x75b5cf9c` 一带（UTF-16 名字表）**；
`data/appmap/app_strings.json` = 1,722 条字符串 → 运行时地址，**可直接当符号表喂 Ghidra**。

**⚠️ 未闭合**：映射覆盖 **29.2%**（未映射处 `app_resolve.py` 会报出前后最近的已映射段）；
占位指针编码公式**未解出**（无法离线还原整份镜像）。
**但这些已经不再是阻塞** —— 直接反汇编运行时转储这条路**已跑通**（见下）。

**✅ 已在运行时镜像上拿到的结果（本地 capstone，`tools/hunt.py` / `tools/dis1.py` / `tools/xref_app.py`）**：

* 镜像里 **842 处「内联符号名 + `bl` 解析服务」调用点**、**789 个 PLC 符号名**，全部解出地址 → `data/appmap/name_calls.txt`；
* **六轴 PLC 变量地址已知**（每个符号唯一一个调用点）：
  ```
  Device.Application.IoConfig_Globals.a1.config.write   0x75b5d588
  Device.Application.IoConfig_Globals.a1.config.read    0x75b5f398
  Device.Application.IoConfig_Globals.a1.read/.write    0x75b600a2 / 0x75b5e2e0
  Device.Application.IoConfig_Globals.a1.DSP402_Statemachine  0x75b603cc / 0x75b5e5ec / 0x75b61156
  a2..a6 同构各一份（全表见 name_calls.txt）
  ```
  解析服务的形态：`bl <*+0x1a>` 紧接 `"符号名\0"`，桩体是 `subw r4, lr, #1; mov lr, r5; ldr r6, [pc,#0x918]`（ARM↔Thumb 互调用，**基址已被重定位**）
  ⇒ **这就是 HANDOVER §4.4 说的"按名字解析"通道，现在可逐点反编译。α1 从"要找到它"变成"已知在哪"。**
* **`.app` 自己就引用了伺服参数路径**：`0x75b09362 = "/tmp/ServoParamsWrite"`（与 HTTP 那个通道同名）、`0x75bcd296 = "ServoParam…"`
  ⇒ **Q1（"那条路是否根本不存在"）有了正面材料**，顺着 `0x75b09362` 追即可。

**下一步（按收益排序，详见 `APP_OFFSET_MAP.md` §6）**：

1. `python tools\dis1.py 0x75b5d588` → 看 `a1.config.write` 解析出的值存进哪个结构（**α1 落地**）；
2. 追 `0x75b09362`（`/tmp/ServoParamsWrite`）→ **Q1**：`.app` 侧到底有没有伺服参数写路径、走不走那条邮箱；
3. 六轴 `config.read/.write` 六个调用点逐个反汇编（同构）→ **Q2**；
4. 需要伪 C 时再上 Ghidra：`-import <镜像> -loader BinaryLoader -loader-baseAddr 0x75a76000`（**12.1.4 的参数形式尚未实测通过**）。


### 其它待办
- **J6 的 20.5°**：机制未明但证明"存储零点可被外部改写" ⇒ 值得追
- `tools/ghidra/decomp.java` 可以继续反编译 `modifyServoParams` POST 分支 / `writeSDOthd`，把写路径的 body 键名（`DAT_000fbfec + 0xfbbda` 那类常量）解出来
- **⚠️ 网络**：2026-09-23 **19:37 前后控制箱 SSH/ping 都不通**（`ssh: connect to host 192.168.5.1 port 22: Connection timed out`）——
  与 9/21 的"本机网段不对"是**不同**现象（本机当时在 192.168.5.2 且刚还在用）。**下次动手前先确认控制箱在线。**

---

## 7. 现场状态与安全

| 项 | 状态 |
|---|---|
| 控制器 | pid 376，已重启，SAFEOP 报警应已清除 |
| J6 `0x1600:00` | **20** ✓ 已还原（RxPDO 映射条目数，**这个值错了 J6 就不响应指令**） |
| J6 `0x607C` | **0** ✓（六轴一致） |
| **J6 读数** | **20.5°**（物理在 ~0）⚠️ |
| `homeEncoder.json` | 我改过最后一条的 J6 值，**备份在 `homeEncoder.json.bak_184604`** |

**⚠️ 安全**：在 J6 读数纠正前**不要发运动指令** —— 控制器以为 J6 在 20.5°，实际在 ~0，指令会让手腕多转 20.5°。

---

## 8. 本会话新增的脚本

`tools/ghidra/list_funcs.java`、`tools/ghidra/decomp.java`、
`tools/app_hdr.py` / `app_rec.py` / `app_syms.py` / `app_io.py` / `app_base.py` / `app_cluster2.py`（.app 容器分析）、
`tools/plt_scan.py` / `dis_real.py` / `dis_get3.py` / `dis_modify.py`（手搓的 ELF 反汇编，**现在可被 Ghidra 取代**）、
`tools/mb_scan.py` / `mb_diff.py` / `mb_wkc.py`（pcap 邮箱分析）、
`tools/sess_*.py`（DSH 会话日志挖掘 —— 可从 `session.jsonl.zstd` 里捞历史问答）
