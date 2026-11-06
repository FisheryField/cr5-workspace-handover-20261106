# 报警 `index=0x86,isOn=1`（id=134「上使能关节位置偏差过大」）反汇编定位报告

分析对象：`D:\mydata\workspace\data\libalgs_framework.so.bin`
（2,324,096 B；ELF32 / ARM / ET_DYN；**未 strip**：`.dynsym` 3149 符号、`.symtab` 14,174 符号，
另有 `.debug_info/.debug_line` 小节）。
地址均为**文件内虚拟地址**。第一个 PT_LOAD 是 `vaddr 0x0 / off 0x0 / filesz 0x1c95ec`（恒等映射），
第二个 `vaddr 0x1da000 / off 0x1ca000`；`.bss` 从 `vaddr 0x1de038` 起、**超出文件**
⇒ **所有运行期数值（阈值表、目标数组内容）静态读不到**。

> **与最初假设的重要出入（已按证据修正）**
> * 置 **0x86** 的**唯一**代码点是 **`ServoControl()` 的 `0x00099c6e`**。
> * `CheckErrorOfDemandAndNext()`（最初的头号嫌疑）置的是 **`0xF8 + 轴号` = 248..253**
>   （「第 N 轴稳态误差过大」），**不是 0x86**。原因是它执行 `add.w r0, r4, #0xf8`。
> * `0x0009208c` **不是**"专用 0x86 setter"，而是**以运行期 `r0` 为 index 的通用 setter 实例**
>   （共 27 个调用点，传 22 种不同 index）。

---

## 0. 结论速览

| 问题 | 答案 | 置信度 |
|---|---|---|
| **谁置 0x86** | **`ServoControl(AxesGroupRef*)` @0x976fc 内的 `0x00099c6e`**（`movs r0,#0x86` → `0x00099c70: bl 0x9208c`）。全镜像 `movs r0,#0x86` 的**穷尽扫描**（正例自检通过）只给出 2 处，另一处在 `OnTCPCmd`，上下文无关 | **很高** |
| **置位原语** | `AlarmSysSetBit(index, isOn)` 的非内联实例 `_Z14AlarmSysSetBitjb.part.95.constprop.584` @**0x0009208c**；index 走**运行期 `r0`**：`lsrs r4,r0,#3` / `and r5,r0,#7` | 很高 |
| **0x86 落在哪** | `gAlarmSysState` @**0x001e28d0**（32 B，`.bss`）→ **`bits[16]` 的 bit6**（掩码 `0x40`） | 很高 |
| **比较什么** | **两个 6×f64 位置数组逐元素作差取绝对值**，与门限比较：`|A[i] − B[i]| > thr` → 置位 | 很高 |
| **门限数值** | **硬编码 `5.0`**（`vmov.f64 d8, #5.000000e+00` @**0x99c3a**） | 很高 |
| **比较两侧** | 两侧都是**运行期数组**：A = `gSysParams` 运行期基址 **0x001ea168 + 0x168 = 0x001EA2D0**，6×f64；B = `*(void**)(.got + 槽 0x144c)`，6×f64 | A **高** / B **中** |
| **"期望"侧性质** | **实时量**（每伺服周期重写的全局数组）。**不是上电零值，也不是持久化标定值。** | 高 |
| **触发时序** | `ServoControl()` 是伺服周期函数（`run.cpp`），因此与"上使能后 0.2–0.3 s"吻合 | 中-高 |
| **0x72(114) 由谁置** | **`ServoControl()` 的 `0x000980a4`**（`movs r0,#0x72`）与 `0x9a18e`。**同函数内共 22 个报警点**，见 §5 全表 | 很高 |

---

## 1. 报警位图原语 `AlarmSysSetBit`（逐条读码）

### 1.1 通用实例 `0x0009208c`

```
符号 .symtab : _Z14AlarmSysSetBitjb.part.95.constprop.584 @0x0009208c  size=804
文件 0x9208a 起字节 : 00 00 | 2d e9 f0 4f | c4 08 | c0 4e | 00 f0 07 05 | c3 b0 | bf 4a | 7e 44 |
                     56 f8 02 e0 | 1e f8 04 10 | 41 fa 05 f3 | db 07 | 00 f1 07 81 | ba 4b |
                     4f f0 01 08 | 08 fa 05 f2 | 40 f2 97 1c | cd f8 ...
```

```asm
0x0009208c  push.w   {r4,r5,r6,r7,r8,sb,sl,fp,lr}
0x00092090  lsrs     r4, r0, #3        ; ★ byte index = index >> 3      （原始字节 c4 08 = lsrs r4,r0,#3）
0x00092092  ldr      r6, [pc,#0x300]   ; lit@0x92394 = 0x00149c68
0x00092094  and      r5, r0, #7        ; ★ bit index  = index & 7       （原始字节 00 f0 07 05 = and r5,r0,#7）
0x00092098  sub      sp, #0x10c
0x0009209a  ldr      r2, [pc,#0x2fc]   ; lit@0x92398 = 0x0000162c  (.got 槽偏移)
0x0009209c  add      r6, pc            ; r6 = .got 基址 = 0x001dbd08
0x0009209e  ldr.w    lr, [r6, r2]      ; lr = gAlarmSysState
0x000920a2  ldrb.w   r1, [lr, r4]      ; r1 = gAlarmSysState.bits[index>>3]
0x000920a6  asr.w    r3, r1, r5
0x000920aa  lsls     r3, r3, #0x1f     ; 把该位挪到符号位
0x000920ac  bmi.w    #0x922be         ; 已经是目标状态 -> 直接返回
0x000920b0  ldr      r3, [pc,#0x2e8]
0x000920b2  mov.w    r8, #1
0x000920b6  lsl.w    r2, r8, r5        ; ★ mask = 1 << (index & 7)
0x000920ba  movw     ip, #0x197        ; ★ 行号 407 —— 与现场日志 "#407" 逐字吻合
0x000920be  str.w    ip, [sp, #4]
...                                    ; 之后是 spdlog 组装：文件串 + 函数串 + 行号 + 格式串
```

`.got` 槽位经 `.rel.dyn` 解析（`tools/algs_got.py`；**[实证, 工具]**，正例：槽 0x162c → `gAlarmSysState`）：

```
slot 0x162c -> gAlarmSysState @0x001e28d0  size=32   (R_ARM_GLOB_DAT, type 21)
```

⇒ 位图 = **`index>>3` 选字节、`index&7` 选位**，32 B = 256 位。
**`0x86 = 134` → 字节 16、位 6 → `gAlarmSysState.bits[16] |= 0x40`。**

日志与文件名串（**[实证, 原始字节检索]**）：

```
0x001abd89  "alarms.h"
0x001abd94  "index=0x%x,isOn=%d"      <-- 与 'index=0x86,isOn=1' 逐字一致
```

**★ 重要澄清**：该实例**不是**"index 被常量折叠成 0x86 的专用克隆"。
它读 `r0` 当 index **并且**把 `r0` 当格式化参数打印，
所以同一份代码被 27 个调用点复用、传 22 种不同 index。

### 1.2 带 `isOn` 形参的实例 `part.104` @0x00196000（size 820）

```asm
0x00196000  push.w   {r4,r5,r6,r7,r8,sb,sl,fp,lr}
0x00196004  lsrs     r4, r0, #3
0x00196006  ldr.w    r8, [pc,#0x310]   ; lit@0x196318 = 0x00045cf2
0x0019600a  and      r7, r0, #7
0x00196010  ldr      r3, [pc,#0x308]   ; lit@0x19631c = 0x0000162c -> gAlarmSysState 槽
0x00196012  add      r8, pc            ; r8 = .got = 0x001dbd08
0x00196014  ldr.w    lr, [r8, r3]
0x00196018  ldrb.w   r2, [lr, r4]
0x0019601c  asr.w    r3, r2, r7
0x00196020  and      r3, r3, #1
0x00196024  cmp      r3, r1           ; ★ isOn 在 r1
0x00196026  beq.w    #0x19623a
0x0019602e  movs     r0, #1
0x00196032  lsls     r0, r7           ; mask = 1<<(index&7)
0x0019603c  orrs     r2, r1           ; ★ isOn(0/1) 直接当 mask 用
0x0019604c  strb.w   r2, [lr, r4]
0x00196042  movw     r1, #0x197       ; 行号 407
```

18 个克隆全部逐条读码：**index 一律走运行期 `r0`**，没有一个是把 index 折叠成掩码的。
差别只在"已置位就返回"的判据（15 个用 `lsls r?,r?,#0x1f` + `bmi`；`part.104`/`part.9`
用 `and #1` + `cmp r3,r1`，后者带 `isOn`）。

### 1.3 `CheckAlarmAndReset(j)` @0x00198674（**[逐条读码]**）

```asm
0x00198674  push     {r3,r4,r5,lr}
0x00198676  lsrs     r5, r0, #3
0x00198678  ldr      r3, [pc,#0x28]     ; lit@0x1986a4 = 0x00043684
0x0019867a  and      r4, r0, #7
0x0019867e  ldr      r2, [pc,#0x28]     ; lit@0x1986a8 = 0x0000162c -> gAlarmSysState 槽
0x00198682  ldr      r3, [r3, r2]
0x00198684  ldrb     r3, [r3, r5]
0x00198686  asrs     r3, r4
0x00198688  ands     r3, r3, #1
0x0019868c  beq      #0x1986a0          ; 未置位 -> 返回 0
0x0019868e  cmp      r0, #0xff
0x00198690  bls      #0x198696
0x00198692  movs     r0, #1
0x00198694  pop      {r3,r4,r5,pc}
0x00198696  movs     r1, #0            ; isOn = 0
0x00198698  bl       #0x196000          ; 清位
```

---

## 2. 决定性证据：0x86 的置位点 = `ServoControl()` @0x00099c6e

### 2.1 穷尽扫描 `movs r0,#0x86`

`movs rD,#imm8` 的 16 位编码 = `00100 Rd imm8`（`r0` → `0x2000|imm8`）。
这是"报警立即数"最可靠的可搜锚点（命中极少，可逐个人工确认）。

**正例自检**（同一扫描器）：`0x74` → `0x9775c`（已知）、`0x72` → `0x980a2`（已知）——**扫描器有效**。

| 站点 | 立即数 | 所在函数 |
|---|---|---|
| **0x00099c6e** | **0x86** | **`_Z12ServoControlP12AxesGroupRef`** ★ |
| 0x000dfb48 | 0x86 | `_Z8DynamicsbR11PreDealData` |
| 0x0019b96a | 0x86 | `_Z8OnTCPCmdPKc` |

（另两处 0x86 的上下文是动力学/TCP 参数校验，与位置偏差无关。**[计数/普查]** 给候选，**[逐条读码]** 给结论。）

### 2.2 `0x00099c70` 周边逐条读码（含字面量池/MVA/.got 解析）

```
tools/algs_annot.py 99bd0 90   →   lit@0x99fe0/… 的 MVA 全部解析为 0x001ea168（运行期 gSysParams 基址）
                                   lit@0x99fe8 = 0x00001920 -> .got 槽 gAlarmSysState
```

```asm
; ===== 进入条件 =====
0x00099be8  ldr      r2, [pc,#0x3f4]     ; lit@0x99fe0 -> MVA 0x001ea168
0x00099bea  add      r2, pc
0x00099bec  ldr.w    r4, [r2, #0x160]    ; r4 = gSysParams[0x160]（一个运行期计数/状态）
0x00099bf0  cmp      r4, #0
0x00099bf2  beq      #0x99cd6            ; =0 -> 整块跳过
0x00099bf4  ldr      r5, [pc,#0x3ec]     ; lit@0x99fe4
0x00099bf6  adds     r4, #1              ; 计数 +1
0x00099bf8  ldr      r3, [pc,#0x3ec]     ; lit@0x99fe8 = 0x00001920 -> .got 槽 gAlarmSysState
0x00099bfa  vmov.f64 d6, #5.000000e-01
0x00099bfe  add      r5, pc              ; r5 = 0x001ea168
0x00099c00  vmov     s15, r4
0x00099c04  str.w    r4, [r5, #0x160]    ; 回写计数
0x00099c08  ldr.w    r3, [sb, r3]        ; r3 = gAlarmSysState
0x00099c0c  vcvt.f64.s32 d7, s15
0x00099c10  vldr     d5, [r3]            ; d5 = gAlarmSysState 头 8 字节（当 f64 用 —— 见 §8 U3）
0x00099c14  vdiv.f64 d6, d6, d5          ; d6 = 0.5 / d5
0x00099c18  vcmpe.f64 d7, d6
0x00099c20  bgt.w    #0x99e30            ; 计数超限 -> 另一支（日志 "Sevro On Success "）
                                          ; 否则（含 d5==0 使 d6=inf 的情况）继续往下

; ===== 数组指针装配 =====
0x00099c24  ldr      r7, [pc,#0x3c4]     ; lit@0x99fec
0x00099c26  add.w    fp, sl, #0x2bc0
0x00099c2a  ldr      r3, [pc,#0x3c4]     ; lit@0x99ff0 = 0x0000144c  -> 另一个 .got 槽
0x00099c2c  add.w    r4, r5, #0x168      ; ★ A 数组 = 0x001ea168 + 0x168 = 0x001EA2D0
0x00099c30  add.w    r5, r5, #0x198      ; 边界 = 0x001ea168 + 0x198 = 0x001EA300
0x00099c34  add.w    fp, fp, #0x14
0x00099c38  add      r7, pc
0x00099c3a  vmov.f64 d8, #5.000000e+00   ; ★★★ 门限 = 5.0
0x00099c3e  ldr.w    r6, [sb, r3]        ; ★ B 数组指针（运行期写入的指针变量）
0x00099c42  str.w    sb, [sp, #0x38]
0x00099c46  mov      sb, r8
0x00099c48  mov      r8, r7
0x00099c4a  mov      r7, r5              ; r7 = 循环上界
0x00099c4c  ldr      r5, [sp, #0x34]
0x00099c4e  b        #0x99c54

; ===== 比较循环 =====
0x00099c50  cmp      r4, r7
0x00099c52  beq      #0x99c9e            ; 到达上界 -> 结束
0x00099c54  vldmia   r4!, {d6}           ; ★ d6 = A[i]   (r4 += 8)
0x00099c58  vldmia   r6!, {d7}           ; ★ d7 = B[i]   (r6 += 8)
0x00099c5c  vsub.f64 d7, d6, d7          ; ★ d7 = A[i] - B[i]
0x00099c60  vabs.f64 d7, d7              ; ★ d7 = |A[i] - B[i]|
0x00099c64  vcmpe.f64 d7, d8             ; ★ 与 5.0 比较
0x00099c68  vmrs     apsr_nzcv, fpscr
0x00099c6c  ble      #0x99c50            ; <= 5.0 -> 下一元素
0x00099c6e  movs     r0, #0x86            ; ★★★ index = 134
0x00099c70  bl       #0x9208c             ; ★★★ 置位 alarm 134
0x00099c74  movs     r2, #0
0x00099c76  movs     r3, #1
0x00099c78  str.w    r2, [fp]             ; 清运行标志
0x00099c7c  str.w    r2, [r8, #0x15c]
0x00099c80  strb.w   r2, [r8, #0x158]
0x00099c84  str.w    r2, [r8, #0x160]     ; 清上面那个计数
0x00099c88  strb.w   r2, [sb]
0x00099c8c  ldr      r2, [sp, #0x4c]
0x00099c8e  strb     r3, [r5]             ; ★ [r5+0..5] = 1  共 6 字节（6 个轴标志）
0x00099c90  strb     r3, [r5, #1]
0x00099c92  strb     r3, [r2]
0x00099c94  strb     r3, [r5, #2]
0x00099c96  strb     r3, [r5, #3]
0x00099c98  strb     r3, [r5, #4]
0x00099c9a  strb     r3, [r5, #5]
0x00099c9c  b        #0x99c50            ; 继续扫下一个元素
0x00099c9e  mov      r8, sb
0x00099ca0  ldr.w    sb, [sp, #0x38]
0x00099ca4  b.w      #0x97db0
```

**元素个数**：`(0x198 − 0x168) / 8 = 6` 个 f64 ⇒ **六轴**。

**语义**：这是"使能后位置偏差"扫描器 ——
`A[i]` 与 `B[i]` 逐元素作差，`|差| > 5.0` 即置报警 **134**，
并把 6 个轴的标志字节置 1、清一组运行标志。

### 2.3 与现场日志的对应

`ServoControl()` 的源文件就是 **`algs/src/common/run.cpp`**，
并且**正是打印现场那三行 `PoseTrace` 的函数**：

| 字符串 | 地址 |
|---|---|
| `algs/src/common/run.cpp` | 0x001af944 |
| `ServoControl`（`__func__`） | 0x001af738 |
| `PoseTrace: gRobotAxisMove.nextPos: ` | 0x001b10bc |
| `SteadyError: (PDO0x6062)Position demand value: ` | 0x001afc2c |
| `SteadyError: gActualPosition: ` | 0x001afc5c |

⇒ 现场四条日志（三行 PoseTrace + `index=0x86,isOn=1`）**全部出自同一函数 `ServoControl()`**；
"上使能后 0.2–0.3 s"与"计数 `gSysParams+0x160` 从 0 开始累积"的节拍一致。
**这是本报告最强的因果链证据（静态推断，未在线验证）。**

---

## 3. 必须纠正的对照结论：`CheckErrorOfDemandAndNext()` 置的是 0xF8..0xFD

符号：`.dynsym 0x000940cc size=1964 _Z25CheckErrorOfDemandAndNextv`
自报名串 `CheckErrorOfDemandAndNext` @0x001af678；源文件串 `algs/src/common/run.cpp` @0x001af944。

```asm
; ---- 前置闸门：6 轴位置量绝对值 vs 逐轴门限（不满足 -> return 0）----
0x000940d2  ldr.w    r7, [pc,#0x6ec]     ; lit@0x947c0 = 0x00147c26
0x000940d6  ldr.w    r3, [pc,#0x6ec]     ; lit@0x947c4 = 0x00001774 -> .got 槽 gSR6Params
0x000940da  ldr.w    r2, [pc,#0x6ec]     ; lit@0x947c8 = 0x0000186c -> .got 槽 gActualVelocity
0x000940de  add      r7, pc              ; r7 = .got = 0x001dbd08
0x000940e0  ldr.w    sb, [r7, r3]        ; sb = gSR6Params       @0x003158e0
0x000940e4  ldr      r2, [r7, r2]        ; r2 = gActualVelocity  @0x003168a0
0x000940e6  add.w    r3, sb, #0x4b0      ; 门限基址 = gSR6Params+0x4B0
0x000940ea  vldr     d7, [r2]            ; 位置[0]
0x000940ee  vldr     d6, [r3]            ; 门限[0]
0x000940f2  vabs.f64 d7, d7
0x000940f6  vcmpe.f64 d7, d6
0x000940fe  bpl      #0x9411a            ; |pos| >= thr -> return 0
...  重复 6 次：位置 disp 0x00,0x08,...,0x28  门限 +0x4b0,0x4b8,...,0x4d8
0x00094188  bpl      #0x9411a

; ---- 主循环 ----
0x0009418a  ldr.w    r1, [pc,#0x640]     ; lit@0x947cc = 0x000015d4 -> .got 槽 gRobotAxisMove
0x00094196  mov      r4, r2              ; ★ r4 = 0  (轴号)
0x0009419a  mov      r5, r2              ; r5 = 0  (isErr)
0x000941a2  add.w    sl, sb, #0x510      ; sl = gSR6Params+0x510 (门限数组)
0x000941b6  ldr      r3, [r7, r1]        ; r3 = gRobotAxisMove @0x003155e8
0x000941ba  mov      r6, r3
0x000941bc  ldr.w    r3, [pc,#0x610]     ; lit@0x947d0 = 0x00001614 -> .got 槽 robotAxesGroup
0x000941c0  ldr.w    r8, [r7, r3]        ; r8 = robotAxesGroup @0x001de834
0x000941c4  ldr.w    r3, [r8]            ; r3 = *robotAxesGroup
0x000941c8  addw     r2, r4, #0x5d5      ; r2 = axis + 0x5D5
0x000941cc  vldmia   r6!, {d7}           ; d7 = A[axis]
0x000941d0  vldmia   sl!, {d5}           ; d5 = 门限[axis]
0x000941d4  add.w    r3, r3, r2, lsl #3  ; &[ *(robotAxesGroup) + 8*(axis+0x5D5) ]
0x000941d8  vldr     d6, [r3]            ; d6 = B[axis]
0x000941dc  vsub.f64 d7, d6, d7          ; ★ 差
0x000941e0  vabs.f64 d7, d7              ; ★ |差|
0x000941e4  vcmpe.f64 d7, d5             ; ★ 与逐轴门限比较
0x000941e8  vmrs     apsr_nzcv, fpscr
0x000941ec  vstmia   fp!, {d7}
0x000941f0  ble      #0x941fc
0x000941f2  add.w    r0, r4, #0xf8       ; ★★★ r0 = 轴号 + 0xF8  →  0xF8..0xFD
0x000941f6  movs     r5, #1
0x000941f8  bl       #0x9208c            ; ★★★ 置报警 = 轴号+0xF8
0x000941fc  adds     r4, #1
0x000941fe  cmp      r4, #6
0x00094200  bne      #0x941c4            ; ★ 6 轴循环
```

**交叉验证（`alarm_controller.json` 本机副本，546 条，UTF-8 BOM-less，`[实证]`）**：

| id | hex | en |
|---|---|---|
| 248 | 0xF8 | The first axis steady state error is too large |
| 249 | 0xF9 | The second axis steady state error is too large |
| 250 | 0xFA | The third axis steady state error is too large |
| 251 | 0xFB | The fourth axis steady-state error is too large |
| 252 | 0xFC | The fifth axis steady-state error is too large |
| 253 | 0xFD | The sixth axis steady-state error is too large |
| **134** | **0x86** | **Position deviation of joint is too large when enabled**（zh_CN: 上使能关节位置偏差过大） |

⇒ `0xF8 + 轴号` 与 248..253「逐轴稳态误差过大」**逐项吻合**
—— 这是"`CheckErrorOfDemandAndNext` 置的是 248..253，不是 134"的决定性证据
（**[逐条读码]** 的 `add.w r0, r4, #0xf8` × **[实证]** 的报警表）。

该函数在 21,189 个 capstone 验证过的调用点里**没有直接 `bl` 调用者**
（正例自检 PASS，故倾向"确实没有"）；可能经函数指针调用。

---

## 4. `AlarmSysSetBit` 调用点全表（回答第 4 问）

用 `movs r0,#imm8` + `bl 0x9208c` 穷尽枚举（`tools/algs_argsites.py`，3 个正例 PASS）：

```
verified bl -> 0x0009208c : 27 sites
POSITIVE CONTROL 0x0009775e r0=116 (0x74) PASS
POSITIVE CONTROL 0x00099c70 r0=134 (0x86) PASS
POSITIVE CONTROL 0x000980a4 r0=114 (0x72) PASS
```

| 站点 | index | 报警表里的含义 | 所在函数 |
|---|---|---|---|
| 0x000924a6 | 0xA1 = 161 | Control mode switching error | `ServoModeSwitch.part.96` |
| 0x000941f8 | 0xF8+轴 = 248..253 | 第 N 轴稳态误差过大 | `CheckErrorOfDemandAndNext` |
| 0x0009775e | 0x74 = 116 | The emergency stop button is pressed | `ServoControl` |
| 0x000977b6 | 0x79 = 121 | Fail to initialize the controller | `ServoControl` |
| 0x00097e1a | 0x74 = 116 | 急停 | `ServoControl` |
| **0x000980a4** | **0x72 = 114** | **Homing error（回零失败）** | **`ServoControl`** |
| **0x00099c70** | **0x86 = 134** | **上使能关节位置偏差过大** | **`ServoControl`** ★ |
| 0x00099d28 | 0x74 = 116 | 急停 | `ServoControl` |
| 0x00099dd0 | 0x85 = 133 | 48V 超级电容充电异常 | `ServoControl` |
| 0x00099dda | 0x84 = 132 | 24V 超级电容充电异常 | `ServoControl` |
| 0x00099de4 | 0x7f = 127 | 反馈板 modbus 连不上 | `ServoControl` |
| 0x00099dee | 0x7e = 126 | 控制板开关被按下 | `ServoControl` |
| 0x00099df8 | 0x7c = 124 | AC 检测板状态错 | `ServoControl` |
| 0x00099e02 | 0x7b = 123 | 反馈板未回上电信号 | `ServoControl` |
| 0x00099e0c | 0x7a = 122 | 接触器断开 | `ServoControl` |
| 0x00099ece | 0x73 = 115 | Fail to enable controller | `ServoControl` |
| 0x00099f52 | 0x82 = 130 | Universal IO board offline | `ServoControl` |
| 0x0009a0d0 | 0x67 = 103 | Joint3 is disabled | `ServoControl` |
| 0x0009a0da | 0x6a = 106 | Joint4 is disabled | `ServoControl` |
| 0x0009a18e | 0x72 = 114 | 回零失败 | `ServoControl` |
| 0x0009a1b4 | 0x83 = 131 | Terminal IO board offline | `ServoControl` |
| 0x0009a204 | 0x61 = 97 | Joint1 Drive State Disable | `ServoControl` |
| 0x0009a20e | 0x76 = 118 | Security I/O is disconnected | `ServoControl` |
| 0x0009a2b2 | 0x64 = 100 | Joint2 is disabled | `ServoControl` |
| 0x00097d00 / 0x00097fd8 / 0x000982ba | 未能回溯（r0 由更早的路径设置） | — | `ServoControl` |

**⇒ 0x72(114)「回零失败」由 `ServoControl` 的 `0x000980a4` / `0x0009a18e` 置位**
（我最初写的"本库不置 0x72"**是错的**，原因是我的 `movs r0,#imm8` 扫描器
在 16 位指令的半字对齐判断上有缺陷——见 §7 教训 3。**该错误已由三个正例自检暴露并修正。**）

---

## 5. 数据来源

### 5.1 `ServoControl` 里 0x86 比较的两侧

| 侧 | 表达式 | 静态可定 | 性质 |
|---|---|---|---|
| A | `r4 = 0x001ea168 + 0x168 = ` **0x001EA2D0**，`vldmia r4!,{d6}` 逐 f64，6 个 | **是**（逐条读码） | `.bss` 内的 f64 数组，每周期重写 |
| B | `r6 = *(void**)(.got + slot 0x144c)`（`lit@0x99ff0 = 0x0000144c`），`vldmia r6!,{d7}` | **否**（运行期指针） | 同上 |

⚠️ **`0x001ea168` 的符号名未确证**：`.dynsym` 里的 `gSysParams @0x00316160`
**不是**这个地址；代码里大量 MVA 都解析到 `0x001ea168`（`.bss` 内）。
**不影响"两个实时 f64 数组作差"这一结论。**

### 5.2 `CheckErrorOfDemandAndNext` 的两侧 + 门限（对照用，符号已实证）

| 量 | 表达式 | `.rel.dyn` 解析（`tools/algs_got.py`） |
|---|---|---|
| A | `gRobotAxisMove + 8*轴`，`vldmia r6!` | 槽 0x15d4 → `gRobotAxisMove` @0x003155e8 |
| B | `*(void**)robotAxesGroup + 8*(轴+0x5D5)` | 槽 0x1614 → `robotAxesGroup` @0x001de834 |
| 门限 | `gSR6Params + 0x4B0 + 8*轴` | 槽 0x1774 → `gSR6Params` @0x003158e0 |
| 别名 | `gActualVelocity` @0x003168a0 = **`gRobotAxisMove + 0x808`** | 槽 0x186c；算术吻合：`0x3155e8+0x808 = 0x315DF0 = 0x3158e0+0x510` |

⇒ `gActualVelocity` 就是 `gRobotAxisMove` 后面紧邻的 200 B 结构，
内部再切成 `+0x510 / +0x538 / …` 等 6×f64 数组。

**门限 `gSR6Params+0x4B0..` 的写入点（逐条读码，`InitRobot` @0x94970，
`_Z9InitRobotP12AxesGroupRef` size 11492）**：

```asm
0x00094f18  vldmia   r7!, {d7}           ; r7 = sl+0x348
0x00094f1e  vldmia   ip!, {d6}           ; ip = sl+0x318
0x00094f22  cmp      r1, #0x30           ; 6 次（每轴 0x30 字节）
0x00094f2c  vdiv.f64 d5, d6, d7          ; ★ 比值
0x00094f30  vstmia   lr!, {d5}           ; ★ 门限数组[axis] = 比值
0x00094f5c  add.w    r3, r3, #0x4d8        ; ★ 每轴描述符 0x4D8 字节
0x00094f60  bne      #0x94f18
...
0x00094f76  vldmia   r2!, {d6}
0x00094f7a  vldmia   r0!, {d7}
0x00094f7e  vmul.f64 d7, d6, d7
0x00094f82  vmul.f64 d7, d7, d5
0x00094f86  vstr     d7, [r3]
0x00094f8a  add.w    r3, r3, #0x4d8
0x00094f90  bne      #0x94f76
```

⇒ 这些门限是**运行期由速度/加速度参数算出的比值**，不是启动常量表
⇒ **"上电零值"与"持久化值"两个假说都被排除**（对这条路径而言）。

---

## 6. 因果链（**静态推断，未在线验证**）

```
伺服驱动器把 0x6062 / 0x6064 以编码器原始计数上报（3.1.5.0 的故障签名）
        │
        ├─ 主控 TxPDO → gRobotAxisMove.nextPos[] / gActualPosition[]   (110.95, -46.65, ...)
        │
        └─ 主控自己算出的另一组位置数组 A = 0x001EA2D0 (6×f64)
                │
                ▼
   ServoControl() @0x99c50..0x99c70（每伺服周期；gSysParams+0x160 计数非 0 时进入）
        |A[i] − B[i]|  >  5.0    （6 轴任一）
                │
                ▼
   AlarmSysSetBit(0x86 /*134*/, 1)  →  gAlarmSysState.bits[16] |= 0x40
                │
                ▼
   6 个轴标志字节置 1 + 清运行标志  →  主控下使能
```

并行路径（若被调用）会置 0xF8..0xFD 的逐轴「稳态误差过大」；
**当前日志是 0x86，所以主导者是上面这条。**

---

## 7. 方法学 / 正例自检（本次踩坑留档）

1. **线性反汇编会在函数间 padding 处静默停止**：第一版"对 `.text` 一次性 `md.disasm`"
   只解出 **51 条**指令（停在 `0x4c3cc` 的 padding）。
   ⇒ 必须按 `.symtab` 函数边界、或按 prologue 种子逐段解码。
2. **手写 Thumb-2 BL/BLX 立即数解码器不可靠（本次最大的时间黑洞）**：
   我试了 6 种位域/偏置组合，与 capstone 的一致率在 0/177 与 177/177 之间反复横跳；
   **同一镜像内不同站点需要的偏置并不自洽**。
   ⇒ **结论：不要手写 Branch 解码器。** 改用
   **prologue 种子 + capstone 前向解码**（`tools/algs_callmap2.py`，
   1755 个种子 → **21,189 个调用点**，正例 `0x941f8 -> 0x9208c` **PASS**）；
   再叠加**全 `.text` BL 形状穷尽扫描 + capstone 逐条确认**兜底
   （`tools/algs_argsites.py`，27 个 `bl 0x9208c` 站点）。
3. **`movs rD,#imm8`（16 位 `0x20xx`）是找"报警立即数"的可靠锚点**，
   但**半字对齐必须走全 `.text` 的 2 字节步长扫描**。
   我第一版只扫了 `.symtab` 中"有 size 的函数范围"和几个 prologue 窗口，
   **漏掉了 `0x980a4` 的 `movs r0,#0x72`**，于是写出了"本库不置 0x72"这个**错误结论**。
   **是三个正例自检（0x74/0x86/0x72）把它抓出来的。**
   ⇒ 教训：**"扫不到"永远不能作为否定结论，除非扫描器已用已知样本自检通过，且扫描范围已穷尽。**
4. **`.got` 槽位必须用 `.rel.dyn` → `.dynsym` 解析**：GOT 静态值是 0（目标是 `.bss`）；
   直接读 GOT 会得到 `0x6a`/`0x4` 这类垃圾值。用 `tools/algs_got.py`
   （正例：槽 0x162c → `gAlarmSysState`）才拿到 `gSR6Params` / `gActualVelocity` /
   `gRobotAxisMove` / `robotAxesGroup` 的真实名字。
5. **PIC 字面量池地址算式**：`ldr rX,[pc,#K]` + `add rX,pc` 得到 MVA；
   随后 `ldr rY,[r7,rX]` 里的 `rX` 是 **`.got` 字节槽偏移**，不是符号地址。
   `tools/algs_annot.py` 把这条链自动解出并打印字符串/MVA/GOT
   （正例：`0x940d6` 槽 `0x1774` → `gSR6Params`）。
6. **反向教训**：**名字/形态吻合 ≠ 同一件事**。
   `CheckErrorOfDemandAndNext`（名字就是"检查给定与下一个的误差"）确实做了
   六轴位置差比较，**但它置的位是 `0xF8+轴`**。
   **把它钉死的是 `add.w r0, r4, #0xf8` 这一条指令 + 报警表 id 248..253 的逐项吻合。**
   若只凭"名字像"下结论，本报告会完全错。

### 本次写出的工具（均带正例断言，失败即 abort）

| 工具 | 作用 |
|---|---|
| `tools/algs_syms.py` | ELF 段/符号总览 + 原始字符串正例自检 |
| `tools/algs_got.py` | `.rel.dyn` → GOT 槽 → 符号名（★关键） |
| `tools/algs_annot.py` | 反汇编 + 字面量池/MVA/GOT/字符串自动注解（★关键） |
| `tools/algs_callmap2.py` | prologue 种子调用图（21,189 站点，正例 PASS） |
| `tools/algs_argsites.py` | 穷尽枚举 `bl <target>` 站点并回溯 r0（3 正例 PASS）（★关键） |
| `tools/algs_offscan.py` | 按结构偏移扫描内存访问（正例 0x4b0 PASS） |
| `tools/algs_fielddump.py` | 大立即数/大位移指令清单 |
| `tools/algs_find.py` | 按符号名查地址并全函数反汇编 |
| `tools/algs_alarmsites.py` | 枚举函数内所有 `AlarmSysSetBit` 调用及其 `r0` |
| `tools/algs_walk.py` | 从任意地址回溯 prologue 再前向反汇编 |
| `tools/algs_dis.py` | 单地址反汇编 + 字面量池解析 |
| `tools/algs_blverify.py` / `algs_blsolve*.py` | 手写 BL 解码器 vs capstone 对拍（**用于证明手写解码不可靠**） |

---

## 8. 我**没能**确定的部分

| # | 不确定项 | 现状 | 影响 |
|---|---|---|---|
| **U1** | `0x001ea168` 的符号名 | 代码里大量 MVA 解析到它；`.dynsym` 的 `gSysParams@0x00316160` **不是**它。在 `.bss` 内，**静态读不到内容**。需在线 dump 或解析 `.debug_info` 的 CU | 不影响"两个实时数组作差"结论 |
| **U2** | `0x99c58` 的 B 数组（`.got` 槽 0x144c）指向哪 | 该槽在 `.rel.dyn` 里**不是 OBJECT 符号** ⇒ 运行期写入的指针变量，静态取不到值 | 中 |
| **U3** | `0x99c10` 的 `vldr d5,[r3]` 把 `gAlarmSysState` 头 8 字节当 f64 当分母 | `gAlarmSysState` 是 32 B 位图（静态全 0）⇒ `0.5/d5 = inf` ⇒ `count > inf` 恒假 ⇒ 计数非 0 后**每周期都进扫描**。但"把位图当浮点除数"语义可疑，`r3` 很可能在此前已被重新装填，**我没回溯到那一步** | 中 |
| **U4** | `0x86` 块的**精确进入条件** | 已知：`gSysParams+0x160`（计数）非 0 → 计数 +1 → `count > 0.5/gAlarmSysState[0..7]` 为真则跳到 `0x99e30`（另一支，会打印 `Sevro On Success `），否则进扫描。`+0x160` 这个计数的**运行期含义**（是谁在什么时候把它写成非 0）未定 | 中 |
| **U5** | 比较元素个数 | `(0x198 − 0x168)/8 = 6`，与"六轴"一致；但 `r4` 在 `0x99c2c` 之前是否被其它分支改写过未穷尽 | 低 |
| **U6** | `AlarmSysCheckAll()` 的位置 | 该串在文件里只出现 3 次（`__func__`），**无符号**；`static inline` 已折叠进各调用点。日志里的 `AlarmSysCheckAll()1` 由 `algs_framework_get_ready_status()`（符号存在）打印 | — |
| **U7** | 磁盘上读不到任何阈值数值 | 相关全局全部在 `.bss`（`vaddr ≥ 0x1de038 > filesz 0x1c95ec`），静态镜像里没有内容。唯一可读的门限数值是硬编码的 **5.0**；`gSR6Params+0x4B0..` 的数值**必须在线 dump** | 高（硬边界，不是没找） |
| **U8** | `0x97d00` / `0x97fd8` / `0x982ba` 三处的 index | r0 由更早的路径设置，窗口内没找到写入点 | 低 |

---

## 9. 置信度总结

| 结论 | 置信度 | 依据 |
|---|---|---|
| `AlarmSysSetBit` 位图语义（`index>>3` 字节 / `index&7` 位）；`gAlarmSysState` 32 B；0x86 → `bits[16]` bit6 | **很高** | 逐条读码 + `.rel.dyn` 符号解析 + 格式串原字节 |
| 置 **0x86** 的代码点 = `ServoControl()` 的 **`0x00099c6e`**（`bl` 在 `0x00099c70`） | **很高** | 逐条读码 + 立即数穷尽扫描（3 正例自检）+ 该函数即 `run.cpp` 的周期函数（与现场日志同 TU） |
| 比较 = `|A[i] − B[i]| > 5.0`，A/B 均为 `.bss` 内 6×f64 运行期数组 | **高** | 逐条读码；B 的具体符号未定（U2） |
| 门限 = **硬编码 5.0** | **很高** | `vmov.f64 d8,#5.000000e+00` @0x99c3a |
| `CheckErrorOfDemandAndNext()` 置的是 **0xF8+轴（248..253）**，**不是** 0x86 | **很高** | 逐条读码 + `alarm_controller.json` id 248..253 逐项吻合 |
| "期望"侧 = **实时量**（周期重写），**不是上电零值、不是持久化值** | **高** | 两侧都是周期刷写的全局；`InitRobot` 运行期计算门限的算式已读出 |
| **0x72(114) 由 `ServoControl` 的 `0x000980a4` / `0x0009a18e` 置位** | **很高** | 逐条读码 + 正例自检（我曾写错成"不在本库"，已更正） |
| `ServoControl` 一个函数里覆盖 **22 种**报警 index（116/121/114/134/133/132/127/126/124/123/122/115/130/103/106/131/97/118/100/…） | **高** | 穷尽枚举 27 个 `bl 0x9208c` 站点 + 回溯 r0 + 报警表逐项对照 |
