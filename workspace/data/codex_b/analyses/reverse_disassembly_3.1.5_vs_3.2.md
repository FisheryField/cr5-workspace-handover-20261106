# 3.1.5 与 3.2.d.8 伺服固件初步反汇编

## 输入

- 3.1.5：`D:/mydata/workspace/data/cabinet/3.1.5_candidate_upgrade/CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin`
- 3.2.d.8：`D:/mydata/workspace/servo_fw/CR5_Servo_ST_FOE_V3.2.D.8_REBUILT.bin`
- 两者均去除 32 字节 FoE 头，以 `0x08010000` 作为应用区基址。

## 已确认

- 两版复位向量均为 `0x0801019d`，均为 Thumb 状态。
- 应用区长度：3.1.5 为 328,860 字节，3.2.d.8 为 338,072 字节。
- 同地址字节大约 94% 不同，差异分散，不是少数连续补丁块。
- 可识别的标准 CiA402 字符串（如 `Home offset`、`Position Offset`、`Speed during search for zero`）两版都存在，不能据此证明 3.2 新增了持久化实现。
- `0x200d` 的字节模式在两版中都出现，但出现位置不同，当前不能把它们直接解释为可访问的 SDO 对象处理函数。

## 初步判断

反汇编已经确认两版共享同一启动入口和相同的 Thumb 固件家族，但应用代码发生大范围重排/增加。当前没有识别出一个可以安全复制到 3.1.5 的独立编码器保存函数。

下一步若继续，需要对两版建立函数边界和调用图，再追踪：

1. 编码器实际位置采样；
2. 回零/校零状态机；
3. 参数对象访问；
4. Flash/NVM 写入与上电恢复。

在这四条链闭合前，不生成补丁、不修改原始固件。

## 控制器侧已连接的关键链

`DataSubProcess::caliHome()` 位于 `libdataSvr.so:0x000F0429`。反汇编显示：

```text
调用伺服 calihome 回调（对象虚表偏移 +0xB8）
等待/检查回调结果
从运行时对象 this+0xE20 取两组 6×double
复制到 this+0x20C0（innerEncoder）
复制到 this+0x20F0（outEncoder）
设置状态并返回
```

其中复制循环的关键地址为：

```text
0x000F0473  source = runtime + 0x3100 + 0x10
0x000F0477  dest   = this + 0x20C0
0x000F047B  source = runtime + 0x3240 + 0x38
0x000F048B  dest   = this + 0x20F0
0x000F048F  ldrd/strd，连续复制六个 double
```

这证明 `homeEncoder.json` 的数据流不是 JSON 文件直接生成零点，而是：

```text
伺服 calihome 回调
→ runtime + 0x3100/0x3240 两组结果缓存
→ caliHome() 复制到 +0x20C0/+0x20F0
→ updateEncoderData() 序列化到 JSON
```

因此 3.1.5 的异常点已经进一步缩小到：**runtime +0x3100/+0x3240 结果缓存没有被正确填充，或者底层参数访问失败后被置零**。

## 新增结论（2026-09-22）

- `robot_control::updateEncoderData()` 只轮询每轴的 calihome 完成标志并统计 `HomeNumdone`，随后触发 `DataSubProcess::updateEncoderData()`；它不负责产生编码器数值。
- 全局指令搜索没有找到其他明确写入 `runtime + 0x3100` 或 `runtime + 0x3240` 的控制器侧函数；这两块更像由伺服/PLC 运行时对象填充的共享结果区。
- 3.1.5 的 EtherCAT PDO 仍出现非零周期数据，说明链路和位置采样并非整体失效；异常更具体地落在“回零结果缓存/持久化返回值”这一支路。
- 因此当前不能把问题归因于 JSON 写文件，也不能安全地把控制器侧 `caliHome()` 改成“强行保留旧值”：那会掩盖伺服回零结果，且可能造成零点错误。

## 3.1.5 固件内部静态追踪进展

3.1.5 应用区仍保留完整的 CiA402 回零/位置对象文本，包括：

- `Speed during search for zero`
- `Home offset`
- `Position Offset`
- `Position actual internal value`
- `Position encoder resolution`

这说明 3.1.5 并非没有回零功能或位置偏置对象；问题更可能是回零完成后的结果提交/保存分支，而不是普通位置采样分支。

当前仅凭无符号裸 bin 还不能安全地给出某个函数地址就是 Flash 写入函数。固件没有符号表，且 3.1.5 与 3.2.d.8 存在大范围代码重排。下一步应以可重复的调用目标为依据，确认 `calihome` 完成标志之后是否调用 NVM 写入，再与 3.2.d.8 的同路径比较。

### 已定位的 3.1.5 Flash 驱动候选

在 3.1.5 应用区发现 STM32F4 风格的 Flash 控制寄存器和解锁序列：

- Flash 控制寄存器基址：`0x40023C00`
- 解锁键：`0x45670123`、`0xCDEF89AB`
- 候选驱动入口约在 `0x08013FC4`
- 擦写/状态轮询辅助函数约在 `0x0801404C`、`0x08014174`

反汇编显示该区域确实执行 Flash 控制位设置、等待完成、清除错误位，并包含按字节/半字/字写入的路径。这证明 3.1.5 具备本地 NVM 写入能力。

但目前尚未证明回零状态机会调用这组驱动。全局直接 `BL` 目标没有发现明显调用，说明上层可能通过函数表、间接调用或中间参数存储层使用它。下一步将追踪这些驱动入口的函数指针引用和调用者，再与 `Home offset` 对象访问路径交叉。

### 与 3.2.d.8 的对应关系

3.2.d.8 也包含同一组 STM32F4 Flash 解锁键和 `0x40023C00/0x40023C10` 控制寄存器，但驱动整体平移到了约 `0x0801435C~0x0801450C`。这说明两版都具备同源的 NVM 驱动框架，不能简单解释为“3.2 新增了 Flash 驱动”。真正差异仍应在调用条件、参数提交或回零状态机分支。
