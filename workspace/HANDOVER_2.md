# HANDOVER_2 —— 2026-09-23 第二轮会话交接（`.app` 映射表 + 伺服固件逆向）

> ⚠️ **本文件之后又开了第三轮，见 `SERVO_PERSIST_FINDING.md`。**
> 第三轮**推翻了本文 §4.1 的"唯一卡点"**：`OD 表项 → 厂商参数地址`不需要从固件里解 ——
> 厂商官方 `data/official/servoCSV/param.csv` 直接给出 259 条映射（工具 `tools/hparam_map.py`）。
> 另：`addr200C01` 是 `H0C.00 故障复位`，**不是**零点参数；两版固件的 flash 存档例程 96.6% 相同
> ⇒ **"版本差异 = flash 持久化"已被否证**。

> 读这份 + `HANDOVER.md`（第一轮）+ `AGENTS.md` 就能接上下文。
> 本会话**只做离线逆向**，没动控制箱、没碰总线。
> 主产出：`APP_OFFSET_MAP.md`（.app 映射）、`SERVO_FW_REVERSE.md` / `SERVO_FW_ALIGN_FINDING.md` / `SERVO_FW_OD_FINDING.md`（伺服固件）。

---

## 0. 一句话现状

**做了两条线，都有硬结果，也都各留了一个明确的"唯一卡点"：**

1. **`Application.app` 的"文件偏移 ↔ 运行时地址"映射表已建成**（原 `HANDOVER.md` §6 B 计划）——
   660 段 / 9 个 Δ 池，附带可双向换算的解析器，**并顺手把 `.app` 里的 PLC 轴参数通道调用点全解出来了**（842 个）。
2. **伺服固件本身**：两包都是真 Cortex-M 镜像，**对象字典元数据表已解出**（97 条，37 条与 CiA402 标准逐条对齐）；
   但**跨版本 diff 被判定不可行**（两版几乎无同源代码），所以 U5 只能靠**单向逆向 3.2.D.8**。

**⚠️ 现场状态：控制箱在 2026-09-23 19:37 前后掉线**（ping/SSH 全不通），现场作业目前不可做。

---

## 1. 设备与访问（不变）

| 项 | 值 |
|---|---|
| 控制器 | `192.168.5.1`，SSH root（`rrun.cmd` / `rscp.cmd` + `.askpass.cmd`） |
| 远端 shell | BusyBox ash：**grep 无 `-b`**、**无 python / perl**、有 `awk` |
| 本机 | 有线 `192.168.110.21`、WLAN `192.168.101.208`；**外网正常**（GitHub 直连 200，**VPN 不需要**） |
| 控制器进程 | `codesyscontrol` **pid 376**（本会话观察值，重启会变） |
| 伺服从站 | slave **3~8 = J1~J6** |

---

## 2. ✅ 线一：`Application.app` 映射表（已交付，可复用）

### 2.1 核心数字

| 项 | 值 |
|---|---|
| 样本 | `data/Application.app`，1,076,068 B，MD5 `8416cf0eee070a640702c077eb904b4e` |
| 运行时镜像 | **`0x75a76000-0x75cb8000`**（maps 里被标成 `[stack:383]` 的那段匿名 `rwxp`，**不是栈**） |
| 主 Δ | **`0x75a95cd0`**（`runtime = file_off + Δ`，池内恒定、跨池跳变；**重启前后一致 ⇒ 可缓存**） |
| 映射规模 | **660 段 / 9 个 Δ 池**，`app_resolve.py --check` → **0/660 失败** |

**`.app` 的本质（已量化）**：**归档 + 加载时重定位**——文件里是低位占位值（`0x0000aaaa` → 运行时 `0x75bc2a2a`），
且**载荷被抽取**（每条记录丢 20/23/27/31 字节的头）⇒ 运行时镜像比文件**小约 3.3%** ⇒ **必须分段，单一基址无解**。

### 2.2 顺手拿到的（**这是本会话最有实用价值的产出**）

运行时镜像里 **842 处「内联符号名 + `bl` 解析服务」调用点、789 个 PLC 符号名**（`data/appmap/name_calls.txt` 全表）。
六轴轴参数通道**每个都有确切地址**：

```
Device.Application.IoConfig_Globals.a1.config.write   0x75b5d588   ← ★ α1 的入口
Device.Application.IoConfig_Globals.a1.config.read    0x75b5f398
Device.Application.IoConfig_Globals.a1.read/.write    0x75b600a2 / 0x75b5e2e0
Device.Application.IoConfig_Globals.a1.DSP402_State…  0x75b603cc / 0x75b5e5ec / 0x75b61156
a2..a6 同构各一份
```
调用形态：`bl <*+0x1a>` 紧跟 `"符号名\0"`，桩体 `subw r4, lr, #1; mov lr, r5; ldr r6, [pc,#0x918]`（ARM↔Thumb 互调用）。
**⇒ 原 `HANDOVER.md` §4.4 说的"按名字解析"通道，现在可逐点反编译。**

**另一条线索**：`.app` 自己就引用了 **`/tmp/ServoParamsWrite`**（`0x75b09362`，与 HTTP 那个通道同名）
⇒ 对 Q1「③ 那条路是否根本不存在」有正面材料。

### 2.3 工具与数据

| 产出 | 位置 |
|---|---|
| 映射表（660 段） | `data/appmap/app_map.json` |
| 换算器 | `tools/app_resolve.py`（`--to-runtime` / `--to-file` / `--coverage` / `--check`） |
| 重建脚本 / 字符串锚点 | `tools/app_map_table.py`、`app_strings_map.py` |
| 运行时转储 | `data/appmap/high_73000000.bin.gz`（**64 MiB @ `0x73000000`**，gzip 6.9 MB） |
| capstone 反汇编 | `tools/hunt.py`、`dis1.py`、`xref_app.py` |
| 控制器侧静态 ARM 工具 | `tools/amrd.c`（转储）、`amscan.c`（搜锚点）、`amdump.c`；Zig 编译 |

### 2.4 ⚠️ 坑（别重踩）

* **`Ghidra 地址 = 0x10000 + 文件偏移` 只对 ELF（`libdataSvr.so`）成立** —— `.app` 不是 ELF，必须用运行时镜像。
* Ghidra 对**平坦镜像**几乎不干活（`-import <elf> -processor ARM:LE:32:Cortex` 能导入，但自动建函数只有 **10 个**）。
* Zig 的 `objcopy` 是精简版（不认 `-I`/`--change-addresses`）⇒ 用 `tools/mkelf.py` 自建 ELF。
* Zig 交叉编译需 `ZIG_GLOBAL_CACHE_DIR` 指到工作区内，否则 `AccessDenied`。
* **`amrd` 只用 `pread(/proc/PID/mem)`，不碰总线**，无 `ecat_*` 那种把从站踢出 OP 的风险。

---

## 3. ✅ 线二：伺服固件逆向（有突破、也有一个明确的"不可行"判定）

### 3.1 文件格式（已解）

```
偏移 0x00  16 B  厂商头：d4 c3 b2 a1 | 12 B 哈希
偏移 0x10   4 B  分类字（两版均 0x00000008）    偏移 0x14  4 B  长度
偏移 0x18   4 B  0x08000000                     偏移 0x1c  4 B  0xFFFFFFFF
偏移 0x20  ...   原始 flash 镜像（Cortex-M 向量表开头）
```

| 包 | payload 起始 | 大小 | 向量表要点 |
|---|---|---|---|
| `CR5_Servo_ST_FOE_V3.2.D.8_REBUILT.bin`（MD5 `8f5a1901…` = 原厂） | **`0x08000000`** | 338,072 B | `SP=0x20017f70` `Reset=0x0801019c` |
| `CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin` | **`0x08010000`**（manifest 假设） | 328,860 B | `SP=0x20017a40` `Reset=0x0801019c` |

**都是真 Cortex-M、明文 Thumb + 单精度 FPU**（熵 6.8 bits/B），**没有加密**。

### 3.2 ★ 突破：对象字典元数据表已解出

**位置**：flash **`0x08024991` .. `0x0802642e`**（6,813 B），**97 条**。
**记录布局**（钉死，`name\0` 之后 6 字节，每字段 2 字节小端、高字节恒 0）：

```
+0  u16 type  0x02=i8 0x03=i16 0x04=i32 0x05=u8 0x06=u16 0x07=u32
+2  u16 bits  8 / 16 / 32
+4  u16 attr  0x0007=读写  0x0087=只读  （另见 0x003f / 0x007f / 0x000f）
```

**与 CiA402 标准逐条交叉验证，37 条全部对齐**（0x6007 / 0x603F / 0x6040-41 / 0x6060-6079 / 0x607A-6086 / 0x6091-92 / 0x6098-99）。

零点相关条目：
```
Home offset              u8  8bit attr=0x0007 rw  std=0x607C  @0x0802537e
Homing method            u8  8bit attr=0x0007 rw  std=0x6098  @0x08025804
Motor calibration date   u32 32bit attr=0x003f rw              @0x08025ff7
Facturer_specified1      u8  8bit attr=0x003f rw              @0x08024ed5
Facturer_specified2      i16 16bit attr=0x003f rw              @0x08024f4f
Speed during search for zero @0x08025851     Homing acceleration @0x08025876
```

**⚠️ 表的局限**：**既没有对象 index，也没有厂商参数地址** ⇒ "表项 → 参数地址"的映射**由代码算或在另一张数组里**。

### 3.3 ❌ 已判定不可行：跨版本 diff（**别再投入**）

| 度量 | 结果 |
|---|---|
| 同地址 4 KiB 块完全相同 | **0** |
| **调用图指纹**（1,233 个调用点的 `BL` 目标集合） | **只有 5 个相同** |
| 排除填充后同地址一致率 | 平均 3.38%，中位 **2.15%**，峰值 21.68%（孤立） |
| 字符串表 | 却**几乎一致**（205 条共同，零点名串逐字相同） |

⇒ 两版**词表共用（CiA402 定义）、实现独立**，**没有共享代码可 diff**。
**曾以为的"21.48% 同源代码块"是假的**——靠**并排反汇编**识破：新镜像那块 80% 是 `0x00` 填充。
**跨固件比相似度必须先排除填充字节**（`servo_hot.py` / `servo_map_diff.py` 原始输出有假阳性）。

⇒ 也**已确认不是**自制包"切割点错"造成的（低 64KB 一致率 1.08%，**反而最低**）。
`3.1.5.hex` 是**完整 1 MiB 转储**（32,897 记录、0 校验错误），但自制包 manifest 的 `start_address` 属于 **assumptions**。

### 3.4 工具与数据

| 产出 | 位置 |
|---|---|
| 带符号 ELF（可导 Ghidra） | `data/servo_fw_samples/elf/{v328d8,v3150}.elf`（`tools/mkelf.py` 生成） |
| OD 表解析 | `tools/od_table.py`（`--raw` / `--dump` / `--filter` / `--json`）→ `od_328d8.json` |
| 名字串定位 / 引用反查 | `tools/od_find.py`、`od_refs.py`、`od_refs2.py` |
| 对齐/差异 | `servo_align2.py`、`servo_sync.py`、`servo_locate.py`、`servo_cg.py`（调用图）、`servo_hot.py` |
| 函数恢复 / 并排反汇编 | `servo_recover.py`（619 函数）、`servo_cmp_region.py`（**识破假热点**） |
| 格式/HEX | `servo_probe.py`、`servo_cm.py`、`hexmap.py` |
| 样本副本 | `data/servo_fw_samples/`（含量化前的 3.1.5.hex、自制包） |

---

## 4. ▶️ 下一步（两个卡点，各一条最短路径）

### 4.1 卡点 A：OD 表项 → 厂商参数地址（伺服线，**U5 的唯一卡点**）

**本轮观察到、但尚未验证的线索**（`SERVO_FW_OD_FINDING.md` §7）：

把名字后的字节按 **9 字节**看，所有 OD 条目都自洽，且**低字节恒为 `0x20`**：
```
Home offset            20 00 | 05(u8) | 08bit | attr=0x0007 | 04
Facturer_specified1    20 00 | 05(u8) | 08bit | attr=0x003f | 07
Modes of Operation D.  20 00 | 02(i8) | 08bit | attr=0x0087 | 04
```
而现场已知编码是 `addr + hex(0x2000+H组号) + 两位十进制(组内序号+1)`
（`addr200C01` → `0x200C:1`、`addr200118` → `0x2001:18`）——
**`0x20` 与地址里的 `0x2000` 高字节同形** ⇒ 很可能就是映射规则。

**三步验证（做完就通）**：
1. 用 9 字节布局重解整表，检查 `04`/`07` 那列是否**连续无重复**；
2. 与现场 `servoParams.json` / `homeEncoder.json` 里出现过的 `0x200C:1`、`0x2001:18` 比对；
3. 对上 ⇒ 确认编码规则，**再从 `Home offset`(0x607C) / `Motor calibration date` 的读写路径找非易失写入点**。

**另一条并行的找法**：`0x08051300-0x08052800` 有 6 个"指向 OD 表内中间"的内联描述符
（`0x080513cc`→`0x08024945`、`0x080513f4`→`0x08024d15`、`0x08052520`→`0x08025f39`、`0x080527a4`→`0x08025eed`、
`0x080527a8`→`0x08025f11`、`0x080527b4`→`0x08025991`），周围是 12 字节一组的规整结构
（其中 `0x09801401` 的低字节 `0x09` 疑似项数，9×4=36 与步长吻合）。**这些描述符的消费者就是要找的代码。**

### 4.2 卡点 B：α1 落地（`.app` 线）

```
python tools\dis1.py 0x75b5d588     # a1.config.write 的调用点，看解析出的值存进哪个结构
```
再来：追 `0x75b09362`（`/tmp/ServoParamsWrite`）→ 回答 Q1「`.app` 侧到底有没有伺服参数写路径」。

### 4.3 现场侧（**控制箱在线后**）

⚠️ **在任何现场操作前先确认控制箱在线**（本会话 19:37 掉线，ping + SSH 全不通；
与 9/21 的"本机网段不对"是**不同**现象——当时本机是 192.168.5.2 且刚还在用）。

---

## 5. 诚实清单（哪些是事实 / 哪些是假设）

**事实**
* `.app` 映射：660 段，`--check` 全通过；主 Δ `0x75a95cd0`；842 个 PLC 名字解析调用点。
* 伺服包格式、两版向量表、明文 Thumb + FPU。
* OD 元数据表结构 + 97 条 + 37 条与 CiA402 对齐。
* 跨版本 diff 不可行（调用图 5/1233、排除填充中位 2.15%、4 KiB 块 0 个全同）。
* `3.1.5.hex` 是完整 1 MiB、校验全通过。

**假设 / 未验证**
* `0x20` 是参数地址编码的一部分（§4.1 三步未做）。
* "两版是不同工具链/分支的独立构建"（最简解释，未证实）。
* 自制包 `start_address=0x08010000`（manifest 自列的 assumption；判别实验显示**不影响**前面的结论）。

**已作废的说法**
* ~~"存在一块 21.48% 同源代码，值得优先阅读"~~ —— **错的**，是 `0x00` 填充造成的假象。
* ~~"两版只差一点，可以 diff 出零点修复点"~~ —— **不可行**。
* ~~"`.app` 必须靠 Ghidra 才能分析"~~ —— capstone 路线已跑通，Ghidra 只在需要伪 C 时才用。

---

## 6. 环境备忘（本会话新增）

* `D:\mydata\workspace\.tools\zig\zig-x86_64-windows-0.14.1\zig.exe` —— 自带 binutils、可交叉编译 ARM 静态二进制。
  用法：设 `ZIG_GLOBAL_CACHE_DIR` / `ZIG_LOCAL_CACHE_DIR` 到工作区内；`zig cc -target arm-linux-musleabihf -Os -static`。
* `D:\software\disassembly\arm-toolchain\` **是空的**（只有 zip），没用上；`ghproj_servo_a` / `ghproj_servo_b` 是本会话建的 Ghidra 工程。
* **不需要下载任何东西、不需要 VPN**（本会话已验证 gh 直连可用）。
* PyGhidra 需要 Python 3.10–3.13，**本机是 3.14.7** ⇒ 尽量用 headless + `.java` 脚本。
