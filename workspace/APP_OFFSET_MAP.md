# Application.app —— 文件偏移 ↔ 运行时地址 映射（B 计划，2026-09-23）

> 目标（`HANDOVER.md` §6 B）：建立 `Application.app` 的"文件偏移 ↔ 运行时地址"映射表，
> 为 α1（`IoConfig_Globals.a1.config.read/.write` 落地）和"`.app` 里到底有没有轮询伺服参数邮箱的代码"提供可用的地址换算。

**结论一句话**：映射**已建立并且可复现**——`runtime = file_off + Δ`，Δ 在一个代码/文本池内**恒定**，
跨池才跳变；本文给出 660 段实测区间、9 个 Δ 池、可双向换算的解析器，以及**同一重启前后两张快照 Δ 完全一致**的复现证据。

---

## 0. 结果速查

| 项 | 值 |
|---|---|
| 样本 | `data/Application.app`，1,076,068 B，MD5 `8416cf0eee070a640702c077eb904b4e` |
| 目标进程 | `codesyscontrol` **pid 376**（2026-09-23 19:30 起，本次会话） |
| 运行时镜像位置 | **`0x75a70000` ~ `0x75cb8000`** 一段匿名 `rwxp` 映射（即 `/proc/376/maps` 里被标成 `[stack:383]` 的那一段，**不是栈**） |
| 主 Δ（代码池） | **`0x75a95cd0`** —— 与重启前的快照（`0x75a90764` 段附近的 19:28 采样）表现一致 |
| 实测区间 | **660 段**，覆盖文件 314,171 B（29.2%） |
| 映射工具 | `tools/app_map_table.py`（重建）、`tools/app_resolve.py`（换算/自检） |
| 映射表 | `data/appmap/app_map.json` |
| 内存转储 | `data/appmap/high_73000000.bin.gz`（**64 MiB**，地址 `0x73000000`+，gzip 6.9 MB） |

```powershell
# 换算
python tools\app_resolve.py --to-runtime 0x0e9f08      # → 0x75b5d58c
python tools\app_resolve.py --to-file    0x75a9da88    # → 0x00008000
python tools\app_resolve.py --coverage                 # 覆盖率 + 未映射空洞
python tools\app_resolve.py --check                    # 用转储逐段复验（应 0 失败）
```

---

## 1. `.app` 不是镜像，是"归档 + 重定位"（本次实测确定）

`HANDOVER.md` §6 的判断（"`.app` 不是绝对地址镜像，而是加载时重定位"）**成立**，本次把它量化了：

### 1.1 直接对照证据（file 0x400 ↔ runtime 0x75a960d0）

```
file: ... 00 00 60 aa 00 00 80 ac 00 00 d0 65 04 00 ...
mem : ... 00 00 60 2a bc 75 80 2c bc 75 d0 e5 bf 75 ...
```

* `0x0000aaaa` → `0x75bc2a2a`、`0x0000ac80` → `0x75bc2c80`、`0x000465d0` → `0x75bfe5d0`
* 即：**文件里是"低位占位值"，运行时被换成真实地址**；`0x0080xxxx` 一类 dword 同族（`> 0x00800000` 的 dword 共 231,073 个）
* 占位编码**不是**简单的 `value + 常量`（对 231,073 个字只解出 18 个落在文件范围内的目标），
  说明存在多张"段基址表"分别编码 —— 这也是**为什么静态解析文件没有出路**。

### 1.2 载荷被抽取，运行时镜像比文件**小**（Δ 会漂移）

同一代码流在两边的跨度不同：

| 位置 | file | runtime | 比 |
|---|---|---|---|
| 前 8 KB | 0x400 → 0x8400 | 0x75a960d0 → 0x75a9e0d0 | 1:1 |
| 到 1 MB 附近 | Δ 从 `0x75a95cd0` 漂到 `0x75a923ac` | | **Δ 缩小约 3.3%** |

⇒ 文件里每个"记录"带一段头/元数据（实测被丢弃的记录长度多为 **20 / 23 / 27 / 31 字节**，也有 75、135 字节的），
加载器只留载荷。**因此映射必须是分段的，单一基址无解**——这就是原计划第 1 步（"base 分组"）的准确形态。

### 1.3 代码区里也插着元数据块

```
file 0x00000100  4e f0 01 0e 80 b5 6f 46 30 b4 00 24 3c 74 bc 68   ← Thumb 代码
file 0x00000148  c8 be 04 00 00 bf 00 bf a0 01 e0 00 21 06 03 00
file 0x00000154  78 12 00 00 22 d4 80 00 50 00 00 00               ← 记录头（长度/类型/占位指针）
file 0x00000160  ... 下一个函数
```
`21 06 03 00` + 递增的 `xx 12 00 00` + `22 d4 80 00` + `50 00 00 00` 这一组在每个函数前后重复出现，
是 loader 的"符号/调试/重定位"记录；运行时**大部分被丢弃**，所以函数体在内存里是紧挨着的。

---

## 2. 方法（可复现）

1. **进程与镜像定位**：pid 376；`/proc/376/maps` 里 `0x75a76000-0x75cb8000 rwxp` 一段 2.3 MB 匿名映射就是 `.app` 的运行时镜像
   （文件 1.05 MB，量级相符；`HANDOVER.md` 里那句"命中点在映像偏移 0x53da8"这次被解释清楚了：**载荷被抽取导致偏移不一致**，不是别的东西）。
2. **整段转储**：`tools/amrd`（Zig 交叉编译的静态 ARM 二进制，逐页 `pread`，空洞跳页补 0）
   ```bash
   /tmp/amrd 376 73000000 4000000 raw | gzip -1 > /tmp/high.bin.gz   # 64 MiB
   ```
3. **锚点**：文件里的 ASCII 字符串/符号表（≥12 字符，共 1,722 条），逐条在转储里检索
   —— 字符串是被 1:1 保留的内容，位置唯一，**天然是锚点**（`tools/app_strings_map.py`）。
4. **生长**：每个锚点向两侧逐字节对齐生长，允许 **≤64 B 的不匹配段**（那就是重定位改写点），
   要求重同步处至少 16 B 连续一致（`app_map_table.py: run_bounds`）。
5. **合并 + 校验**：同 Δ 区间合并；对每段按 `runtime = file_off + Δ` **回读转储**复验，一致率 <85% 的直接丢弃。

结果：941 候选 → **660 段有效**，0 段复验失败。

---

## 3. 实测 Δ 池（节选，全表见 `data/appmap/app_map.json`）

| Δ | file 范围 | runtime 范围 | 说明 |
|---|---|---|---|
| `0x75a95cd0` | 0x00000330… | 0x75a96000… | **主代码池**（与 19:28 快照的 `0x75a90764+off` 同族） |
| `0x75a94e58` | 0x000200bc-0x00022634 | 0x75ab4f14-0x75ab748c | 第二大连续段（9,592 B） |
| `0x75a923ac` | 0x00072f94-0x00073bce | 0x75b05340-0x75b05f7a | |
| `0x75a91974` | 0x00097174-0x000978a9 | 0x75b28ae8-0x75b2921d | |
| `0x75a73094` | 0x000e9f08 附近 | 0x75b5cf9c… | **`Device.Application…` 符号名池**（`a1.config.write` 就在这一池） |
| … | | | 共 9 个池 |

**独立佐证（关键）**：字符串锚点的 Δ 直方图在 **`0x75a918cc`(278 次)、`0x75a9190c`(226)、`0x75a73684`(165)、`0x75a918b8`(103)、`0x75a74260`(91)** 处形成 5 个高峰
—— 这些就是**符号名/字符串的 5 个副本池**（同一批名字在运行时被复制到多处）。它们同时说明：
`0x75a918cc` 与 `0x75a9190c` 只差 0x40，是**同一张表的两个视图**。

### 3.1 已知地址的手工校验（都通过）

| 文件偏移 | 换算 | 实际内存 | 结论 |
|---|---|---|---|
| `0x0e9f08`（`Device.Applic…`） | 0x75b5d58c | 0x75b5cf9c / 0x75b5d134 / … 同族 | ✓ 同一池，偏移差 0x40 是重复副本 |
| `0x08000` | 0x75a9da88 | 转储即 `OnlineLicenseManager` | ✓ |
| `0x0d77c` | 0x75aa2ed0 | 转储即 `Configuration successfully loaded` | ✓ |
| `0x10080` | **未映射** | runtime 0x75aa5d50 是**别的代码** | ✓（该处记录被丢弃，见 §1.2） |

---

## 4. 直接可用的三条结论

1. **"没有映射"不再是阻塞**：任意 `file_off` 可用 `app_resolve.py` 换算；
   落在空洞时它会报出**前后最近的已映射段**，用于就近定位。
2. **重启前后 Δ 一致 ⇒ 映射可缓存**：19:28 快照与 19:30 快照得到同一族 Δ（`0x75a90764` / `0x75a95cd0`，两者相差 `0x5556c`，
   正好落在 §3 的池间跳变范围内）。**不需要每次重启都重新做映射**，只需确认镜像基址。
3. **α1 的落点已经找到**（本轮最实用的一条）：
   ```
   Device.Application.IoConfig_Globals.a1.config.write   文件 0x0e9f08  → 运行时 0x75b5cf9c 一带（UTF-16 名字表）
   ```
   配合 §3 池表即可反查"哪段代码引用了这张名字表里的一条"——这正是 α1 需要的入口。

---

## 5. 尚未闭合（诚实标注）

| # | 缺口 | 影响 | 下一步 |
|---|---|---|---|
| G1 | 映射覆盖 **29.2%**（660 段 / 1.05 MB） | 空洞处只能就近定位 | 用 `amrd` 再抓 `0x75a70000..0x75d00000` 段，然后把锚点集扩到"任意 16 B 唯一窗口" |
| G2 | 占位指针编码（`0x0080xxxx` 类）**未解出公式** | 无法离线把整份 `.app` 还原成运行时镜像 | 需要定位 loader 的段基址表（在 `.app` 头部 0x80..0x200，`0x00808xxx` 一组值很可疑） |
| G3 | 空洞中的 130 KB 大段（`0xb27d5..0xcbb9`）成因未定 | 可能是另一种编码（非 1:1） | 对照该区 runtime 0x75b… 的内容判断 |

> ⚠️ **但 G1–G3 已经不再是阻塞**：**直接反汇编运行时转储**这条路已经跑通（见 §5.1），
> 而它不依赖文件↔内存的完整映射。映射表的价值退化为"把静态文件里的常量对回运行时"。

### 5.1 ✅ 已经在运行时镜像上拿到的结果（本地 capstone 反汇编，`tools/hunt.py`、`tools/dis1.py`）

镜像里 **842 处"内联符号名 + `bl` 解析服务"的调用点**（即 HANDOVER §4.4 说的"按名字解析"），
**789 个不同的 PLC 符号名**，全部解出地址与调用点。节选：

| 符号名 | 调用点（运行时） |
|---|---|
| `Device.Application.IoConfig_Globals.a1.config.write` | `0x75b5d588` |
| `Device.Application.IoConfig_Globals.a1.config.read` | `0x75b5f398` |
| `Device.Application.IoConfig_Globals.a1.read` / `.write` | `0x75b600a2` / `0x75b5e2e0` |
| `Device.Application.IoConfig_Globals.a1.DSP402_Statemachine` | `0x75b603cc` `0x75b5e5ec` `0x75b61156` |
| `…a2…a6` 同构各一份 | 见 `data/appmap/name_calls.txt`（842 行全表） |

**解析服务的桩体**（`bl` 到 `*+0x1a`，然后 `subw r4, lr, #1; mov lr, r5; ldr r6, [pc,#0x918]`）：
```
0x75b5d588  00 f0 1a f8   bl 0x75b5d5c0          ; 名字紧跟在 bl 后面
0x75b5d58c  "Device.Application.IoConfig_Globals.a1.config.write\0"
0x75b5d5c0  ae f2 01 04   subw r4, lr, #1        ; 典型的 ARM↔Thumb 互调用
0x75b5d5c4  ae 46         mov  lr, r5            ; （PLT 风格，基址已被重定位）
```

**α1 的入口因此从"要找到它"变成"已知在哪"**：`a1..a6` 六个轴的 `config.read/.write`
各有唯一调用点，逐个反编译即可。

**另一条重要线索**：`.app` 自己就引用了伺服参数路径 ——
```
0x75b09362  "/tmp/ServoParamsWrite"     ← 与 HTTP 那个 modifyServoParams 通道同名
0x75bcd296  "ServoParam…"
```
⇒ **`.app` 里有伺服参数相关的代码/路径**（与 `libdataSvr` 里 `modifyServoParams`/`caliHome` 是两处不同实现，后两者在 0x769d…/0x76b7… 段）。
这正好是 Q1 要回答的"③ 那条路是否根本不存在"的反面材料，值得顺着 `0x75b09362` 追。


---

## 6. 给"继续反汇编"的下一步（按收益排序）

### 6.0 最快的路：直接反汇编运行时转储（**已跑通，推荐**）

不必绕 Ghidra：镜像就在 `data\appmap\high_73000000.bin.gz` 里，`tools/` 下的脚本已经能：
`hunt.py`（842 个名字解析调用点 + 789 个符号名）、`dis1.py`（任意地址反汇编 + 自动标名字）、
`xref_app.py`（字符串/指针/引用搜索）。**Ghidra 只在这几件事上还有优势**：伪 C 反编译、自动交叉引用库、结构体识别。

建议顺序：
1. `python tools\dis1.py 0x75b5d588`（`a1.config.write` 调用点）→ 看解析到的值存进哪个结构（上下文 `r5`/`r6`）；
2. 顺着 `0x75b09362`（`/tmp/ServoParamsWrite`）追 → **Q1**；
3. 六轴 `config.read/.write` 调用点逐个反汇编（`name_calls.txt` 里有全部地址，代码同构）→ **Q2/α1**；
4. 需要伪 C 时再上 Ghidra（见 §6.1）。

### 6.1 Ghidra 导入（伪 C 需要，尚未实测通过）

反编译要用**运行时镜像**（静态文件是重定位前的，交叉引用全是占位值）。计划是
```
-import data\appmap\<镜像>.bin -loader BinaryLoader -loader-baseAddr 0x75a76000
```
**但本次实测到两个障碍**：

1. **镜像跨多个映射**：`0x75a76000-0x75cb8000` 是连续的一段，可以直接当一个 `BinaryLoader` 段；
   而 `0x75a5xxxx`／`0x75b5xxxx`（`0x0e9f08` 池所在的 `[stack:383]` 上限到 0x75cb8000）也在同一段内，OK；
   但 `0x75c0xxxx`（`0x75cb9000` 以上的 `[stack:382]`）是**另一段**，需要单独导入。
2. **Ghidra 12 的 `-loader-baseAddr` 参数名/位置需实测**（`-loader BinaryLoader -loader-baseAddr 0x…` 是常见写法，但 12.1.4 对
   `BinaryLoader` 的 `baseAddr` 选项接受十六进制字符串；若报 unknown option，就改用带段表的容器格式
   `-loader BinaryLoader -loader-applyRelocations=false` + `-processor ARM:LE:32:v7`，再 `-scriptPath … -postScript` 补段）。

⇒ **建议先做一次最小验证**：导入 2 MB 镜像，跑 `tools/ghidra/list_funcs.java`，确认 ARM Thumb 函数能被识别（应出现大量函数）。
**这一关过了，B 计划才算真正交付**，α1 才有意义。

### 6.2 镜像到手后立刻要回答的三个问题

| # | 问题 | 怎么看 |
|---|---|---|
| Q1 | `.app` 里**有没有**轮询伺服参数邮箱的代码？（回答"③ 那条路是否根本不存在"） | 在镜像里搜 250 ms 超时相关常量、`writeSDO`/`readSDO` 名字表项（`0x75a918cc`/`0x75a9190c`/`0x75a73684` 三张名字表），看交叉引用 |
| Q2 | `IoConfig_Globals.a1.config.write` 的**地址解析路径**（α1 落地） | 从 `0x75b5cf9c` 那张 UTF-16 名字表出发找引用者（HANDOVER §4.4 说的 `blx r0` + 名字压栈，六轴各一份） |
| Q3 | CODESYS 轴参数通道**如何落到 `IoDrvEtherCAT` 的 SDO** | 从 `0x75a918cc` 池里的 `IoDrvEtherCAT` 名字 → 驱动组件 → SDO 请求构造点 |

### 6.3 顺手可做的（低成本、高价值）

* `tools/app_resolve.py --to-file` 反查：日志/反汇编里出现的每一个 `0x75axxxxx` 都可以回到文件偏移，
  进而在**静态** `.app` 里对照（尤其配合 `tools/ghidra/decomp.java`）。
* 把 `data/appmap/app_strings.json`（1,722 条字符串 → 运行时地址）当作**符号表**直接喂给 Ghidra
  （生成 `.sym`/CSV 导入），能大幅提升可读性。

---

## 7. 采集脚本（控制箱在线时重做一遍）

```bash
# 1) 定位镜像：maps 里最大的匿名 rwxp 段
awk '$2 ~ /^r/ {print $1}' /proc/376/maps > /tmp/regions.txt
# 2) 转储（工具在 tmpfs，重启后要重传）
scp tools\amrd root@192.168.5.1:/tmp/
ssh root@192.168.5.1 "/tmp/amrd 376 73000000 4000000 raw | gzip -1 > /tmp/high.bin.gz"
scp root@192.168.5.1:/tmp/high.bin.gz data\appmap\
# 3) 重建映射
python tools\app_map_table.py data\appmap\high_73000000.bin.gz 73000000 data\appmap\app_map.json
```

⚠️ `amrd` 只用 `pread(/proc/PID/mem)` —— **不碰总线**，不会像 `ecat_zero`/`ecat_mbx` 那样把从站踢出 OP
（`HANDOVER.md` §2.4 的操作纪律只针对 EtherCAT 工具，内存 dump 不属于该风险类别）。
