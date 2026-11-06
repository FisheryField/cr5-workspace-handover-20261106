# 伺服固件逆向 —— 起步记录（2026-09-23）

> 目标：反汇编伺服固件本身，回答 **U5「3.2.D.8 到底改了什么」**（`AGENTS.md` §6 把它列为未解机制问题）。
> 本文只记录**已实证**的内容与**工具链状态**，不确定的地方明确标注。

---

## 1. 结论速览

| 项 | 结论 | 证据 |
|---|---|---|
| 两个固件包是不是**真 Cortex-M 镜像**？ | **是** | 0x20 字节 FoE 头之后就是 `0x08000000` 起的 flash 镜像，向量表完整（SP/Reset/NMI/HardFault/…/SysTick） |
| 代码是否加密/混淆？ | **不是，明文 Thumb** | 熵 6.8–6.9 bits/byte；`0x08010000` 处即正常 VFP 序言（`ee3a0a08 vmov` / `ed948a40 vldr`） |
| 带 FPU？ | **是**（Cortex-M4F 级） | 大量 `vmov/vldr/vstr/vmul` 单精度指令 |
| 两包的 flash **起点是否相同**？ | **不同**（这是最容易踩的坑） | 3.1.5.0 包 manifest 明确 `start_address=0x8010000`；3.2.D.8 包 payload 从 `0x08000000` 起 |
| 两版是"小补丁"吗？ | **不是** | 向量表**逐项不同**；同一地址的 4 KiB 块字节一致率只有 **~2%**（详见 §3 与 §5 的诚实说明） |
| 缺什么才能做可靠的函数级 diff？ | **可靠的函数边界/内存布局** | Ghidra 对平坦镜像自动分析只认出 **10 个函数**；线性扫描在数据区会失步 |

---

## 2. 文件格式（已解）

```
偏移 0x00  16 B  厂商头：d4 c3 b2 a1 | 12 B 哈希/校验
偏移 0x10   4 B  分类/类型字（两版均为 0x00000008）
偏移 0x14   4 B  长度（小端；3.2.D.8 = 0x00050498 = 338072-0x20；3.1.5.0 = 0x0005049c = 328860-0x20）
偏移 0x18   4 B  0x08000000
偏移 0x1c   4 B  0xFFFFFFFF
偏移 0x20  ...   原始 flash 镜像（Cortex-M 向量表开头）
```

| 包 | payload 起始 flash | payload 大小 | 向量表 |
|---|---|---|---|
| `CR5_Servo_ST_FOE_V3.2.D.8_REBUILT.bin` | `0x08000000` | 338,072 B | `SP=0x20017f70` `Reset=0x0801019c` `NMI=0x08017508` `HardFault=0x08015bf8` `SVCall=0x08019c98` `PendSV=0x080189d4` `SysTick=0x0801b29c` |
| `CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin` | `0x08010000`（manifest） | 328,860 B | `SP=0x20017a40` `Reset=0x0801019c` `NMI=0x080170d0` `HardFault=0x0801585c` `SVCall=0x08019640` `PendSV=0x0801859c` `SysTick=0x0801ac44` |

**共同点**：`Reset` 都在 `0x0801019c`；`0x08000020-0x08000040` 有 20 字节在两边**完全相同**；
⇒ 提示存在**共享代码**（共用 bootloader/启动路径）；但**其余向量全部不同**，所以不是同一个二进制。

---

## 3. 差异测量（含方法与不确定性）

| 方法 | 结果 | 说明 |
|---|---|---|
| 同地址 16 字节块精确匹配 | **0.59%** | 全局位移 0 |
| 全文件搜索最佳位移 | 最好也只有 **7.8%**（`+0x1470`） | 说明**不存在单一位移**能对齐，代码被插入/重排 |
| 同地址 4 KiB 块字节一致率 | **1–14%**，多数 ~2% | 逐块图见 `tools/servo_map_diff.py` 输出 |
| 字符串表 | **几乎完全一致**：3.2.D.8 有 261 条"像人话"的串，3.1.5.0 有 214 条，**共同 205 条**；NEW 独有的 56 条**全是代码字节噪声**（不是新字符串） | 见 §4 |
| capstone 函数边界扫描 | 3.2.D.8 = **458** 个起点；3.1.5.0 = **457** 个 | 由 1,233 个 `BL` 目标 + 向量表播种 |

⚠️ **诚实标注**：上面"同地址一致率 ~2%"与"37% 函数逐字节相同"**互相矛盾**，
根因是**函数边界不可靠**（线性扫描遇到数据/字面量池会失步，把大片区域当成一个"函数"，导致匹配率失真）。
**在拿到可靠的内存布局或符号之前，任何"相似度百分比"都不该被引用。**

---

## 4. 字符串层面的可用情报（已确认）

伺服固件里是**标准 CiA402 / EtherCAT 对象字典名称**，两版共有。与零点/标定相关的有：

```
'Home offset'                    'Motor calibration date'
'Position Offset'                'Encoder increments'
'Torque Offset'                  'Encoder increments per second'
'Velocity Offset'                'Position encoder resolution'
'Speed during search for zero'   'Velocity encoder factor'
'Drive manufacturer'             'Dobot EtherCAT Servo Drives'   <- 厂商身份串
'Device name'  'Hardware version'  'Drive catalog number'
'Facturer_specified1' 'Facturer_specified2'                       <- 厂商自定义对象
'Position encoder resolution'    'Feed constant'  'Gear ratio'
```

⚠️ **重要**：`'Home offset'`、`'Motor calibration date'`、`'Encoder increments'` 等**两版都有且字符串完全相同**
⇒ 与 `AGENTS.md` §6 里"两版 OD 名称表各 159 条、完全相同"的离线检验**一致**。
**没有任何"新增对象名"能解释 3.2.D.8 的修复** ⇒ 进一步支持"修复发生在驱动器内部行为，不是新对象"。

---

## 5. 工具链（**零下载**，全部已装）

| 工具 | 位置 | 用途 |
|---|---|---|
| Ghidra 12.1.4 | `D:\software\disassembly\ghidra\` | 有 `ARMCortex.pspec` / `ARM8m_le`（Cortex-M 支持） |
| JDK 21 | `D:\software\disassembly\jdk21\` | Ghidra 依赖 |
| **Zig 0.14.1** | `D:\mydata\workspace\.tools\zig\` | **自带 binutils**（`zig objcopy/objdump`）；注意其 `objcopy` 是精简版，不接受 `-I`（用长选项也缺项）⇒ 我改用 Python 自建 ELF |
| capstone / pyelftools / keystone / unicorn | 系统 Python 3.14 | 反汇编/ELF/汇编/仿真 |
| ⚠️ `arm-toolchain` 目录 | `D:\software\disassembly\arm-toolchain\` | **是空的**（只有 `arm-toolchain.zip`），没用上 |

### 新增脚本（`tools/`）

| 脚本 | 作用 |
|---|---|
| `servo_probe.py` | 识别包格式（头/向量表/熵/版本串） |
| `servo_cm.py` | 解向量表、flash↔文件偏移、指定地址反汇编 |
| `mkelf.py` | **原始镜像 → 带符号 ELF32-ARM**（`.text @0x08000000`、向量表入口做成 `Reset_Handler` 等符号） |
| `servo_funcs.py` | capstone 函数边界扫描（BL 目标 + 字面量池指针播种） |
| `servo_fdif.py` | 函数级 diff（逐字节 / 指令形状 两级匹配） |
| `servo_txt.py` / `servo_sdiff.py` | 字符串层面对比（含"像人话"过滤，去掉代码噪声） |
| `servo_locate.py` / `servo_sync.py` / `servo_map_diff.py` | 对齐定位与逐块差异图 |

### 已产出

* `data/servo_fw_samples/elf/v328d8.elf`、`v3150.elf`（带符号、可被 Ghidra/readelf 正确接受）
* `data/servo_fw_samples/funcs_328d8.json`、`func_diff.json`
* Ghidra 工程：`D:\software\disassembly\ghproj_servo_a`（3.2.D.8）、`ghproj_servo_b`（3.1.5.0）

---

## 6. 已知坑（重复劳动请先读这段）

1. **两个包起点不同**：拿 payload 直接逐字节比对会得出"94% 不同"的**错**结论（0x08000000 vs 0x08010000）。
2. **Ghidra 对平坦镜像几乎不干活**：`-import <elf> -processor ARM:LE:32:Cortex` 能导入成功，
   但自动分析只建了 **10 个函数**（`Function Start Search` 没有种子——向量表是数据、没有导出符号）。
   ⇒ 要先**自己播种**：把向量表入口和 `BL` 目标登记为函数（`servo_funcs.py` 已在做），
   再考虑用 Ghidra 脚本强制反汇编 + 建函数。
3. **字符串 diff 会被代码噪声污染**：代码字节里成片的 `A-Za-z` 会伪装成字符串（如 `'@TDETDETDA'`）。
   `servo_txt.py` 的严格过滤器（字母占比 ≥75%、必须含元音、禁止重复 4-gram）能滤掉绝大多数。
4. **Zig 的 objcopy 是精简版**（`-I`/`--change-addresses` 不支持）⇒ 用 `tools/mkelf.py`。

---

## 7. 下一步（按价值排序）

1. **播种式函数恢复**（最高优先）：用向量表 + `BL`/`BLX` 目标 + 字面量池指针做递归下降，
   在 Ghidra 里强制反汇编并建函数，再产出**可信**的函数清单。**这是让所有 diff 数字变得可信的前提。**
2. **两版函数级对齐**：以"逐字节相同"为强锚点做函数配对，只对**未配对**的函数做指令级对比 ——
   U5 的答案应该就在那批函数里。
3. **重点区域定向反汇编**：CiA402 状态机（`0x6060/0x6040/0x607A/0x6064` 访问点）、
   厂商对象（`Facturer_specified1/2`）读写路径、`Home offset` 的持久化路径（flash 写入点）。
4. **可选下载**（目前不需要）：STM32 **SVD**（外设寄存器命名，先要确定具体型号）、**CMSIS 头**（伪 C 类型）。

⚠️ 全部工作**本地离线**，不需要控制箱、**不碰总线**（与 `/proc/mem` dump 一样属于无风险读取）。
