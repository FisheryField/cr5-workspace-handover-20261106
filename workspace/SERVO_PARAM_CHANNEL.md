# 伺服参数外部通道 —— 进展（2026-09-23 16:5x）

> **结论（回答"3.1.5.0 有没有外部写入捅到"）：有，而且是控制器自带的，不需要维护工具、不需要密码。**

---

## 1. 接口

| 端点（明文 HTTP，端口 22000） | 用途 | 实测 |
|---|---|---|
| `POST /settings/readServoParams` | 读伺服参数 | 200 `{"status":true}` |
| `POST /settings/modifyServoParams` | 写伺服参数 | 未测 |
| `GET  /settings/readServoParams` | 取回结果 | `{"status":false}` |

维护工具的密码门禁**只在客户端 UI**，服务端直接接受请求。

## 2. 请求体信封 —— **已确认**

```json
{"body": [ {"key": "<参数地址串>", "servoNum": <轴号>}, ... ]}
```

**验证方法**：读主控里 `libdataSvr` 的全局量 `SDOWRCount`（ELF 符号 `0x277edc`）：

| 发送的 body 元素数 | `SDOWRCount` |
|---|---|
| 1 | 1 |
| 3 | 3 |
| 5 | 5 |

**三次全部吻合 ⇒ 信封格式正确，`SDOWRCount` = body 数组长度。**

（读取方法：`base = libdataSvr 在 /proc/<pid>/maps 的首地址`，地址 = `base + 符号 st_value`。
注意 `dd` 的统计信息会混进 `od` 输出，只取前几字节。）

## 3. 元素字段（从工具代码反汇编得到）

`DobotProtocol::postSettingsReadServoParams(QString, DobotType::StructSettingsServoParams)` @0x7ad40：

```asm
mov ecx, [eax]        ; QString #1  → "key"
mov ecx, [eax+4]      ; QString #2
fld qword [eax+8]     ; double     （参数值）
movzx eax, byte [eax+0x10]  ; bool （只读标志 —— 对应 servoReadOnlyAddress）
"key" (0x54e5fa) / "servoNum" (0x54e5fe) / "body" (0x54e5f5)
```

## 4. 参数地址编码（推定）

从工具里 `paramIndexToAddress` 产出的 `completeAddress`（`200001`/`200101`/`200406`/`200501`）反推：

```
地址 = sprintf("%x%02d", 0x2000 + H组号, 组内序号)
⇒ SDO 索引 = 0x2000 + H组号 ，子索引 = 组内序号
⇒ H01.17（组01第18项） → 0x2001 : 18
```

**这与最早 E12 推的地址一致**（中途我误以为是自己臆造的而收回，其实是对的）。

## 4.5 工具侧调用链（路线 B 的成果，2026-09-23 17:0x）

用 **E8 操作码字节扫描**（不受反汇编对齐影响）找到真正的调用点：

| 调用者 | 调用地址 | 目标 |
|---|---|---|
| `MainWidget2::initServoParamsWidget(){lambda#0}` @0x600f0 | **0x60897** | `postSettingsReadServoParams` ← **「读取」按钮** |
| `MainWidget2::delegateServoParamsTable(){lambda(int)#2}` | 0x5f42f | `postSettingsReadServoParams`（按行读） |
| `MainWidget2::initUpgradeWidget(){lambda#4}` | 0x5ab67 | `postSettingsReadServoParams`（升级后回读） |
| `MainWidget2::initServoParamsWidget(){lambda#5}` @0x63dc0 | **0x6469a** | `postSettingsModifyServoParams` ← **「写入」按钮** |
| `MainWidget2::delegateServoParamsTable(){lambda(int)#1}` | 0x5e758 | `postSettingsModifyServoParams` |
| `MainWidget2::initUpgradeWidget(){lambda#3}` | 0x5833c | `postSettingsModifyServoParams` |

读按钮的调用点上下文：

```asm
0x060850  mov ecx, [ebp-0x78]        ; 从 UI 表格取
0x060853  mov ebx, [edx+0x34]        ; DobotProtocol 对象
0x060872  call 0x121050              ; 构造 StructSettingsServoParams
0x060897  call 0x7ad40               ; postSettingsReadServoParams(QString, struct)
0x0608bc  test bl, bl
0x0608be  jne  0x609b2               ; 成功
0x0608e1  "读取失败!"                 ; 失败提示
```

（另注：这两个函数的地址在文件里只出现在 **DWARF 调试信息**中（段 /29、/91），
代码里没有绝对引用、也没有直接的 `call rel32` 被我的首轮扫描漏掉——用 E8 字节扫描才找到。）

## 5. 卡在哪

| 现象 | 含义 |
|---|---|
| `SDOWRCount` 正确置位 | 信封 OK |
| **`AllSDOWRInfo`（115200 B 描述表）全 0** | **描述符没被填充** |
| **日志无 `sdo read,slave=…`** | **真正的 SDO 一次都没发** |
| `IsExistSDOWRThd = 0` | 那个"已存在写线程"的标志**没卡住**（日志里那句 `exist sdo wr thd` 是无条件打印） |

⇒ **信封通了，元素内容还没被接受，或者 SDO 线程启动还需要别的条件。**

## 6. 控制器侧关键符号（libdataSvr.so）

| 函数/变量 | 地址 |
|---|---|
| `DataSubProcess::readServoParams(evhttp_request*,void*)` | 0xf9cdd |
| `DataSubProcess::modifyServoParams(evhttp_request*,void*)` | 0x11a1ad |
| `DataSubProcess::parseAndReqGetServoParams(..., rapidjson::Document&)` | 0xec03d |
| `DataSubProcess::parseAndReqSetServoParams(..., rapidjson::Document&)` | 0xebaf5 |
| `IsExistSDOWRThd` / `SDOWRThd` / `SDOWRCount` / `AllSDOWRStatus` | 0x277ed1 / 0x277ed4 / 0x277edc / 0x277ed8 |
| `AllSDOWRInfo` (115200 B) | 0x285fe0 |

日志串表（0x20b7e8 起）：`body` / `key` / `servoNum` / `J1`..`J6` / `the key {} is error.` /
`start read sdo from codesys.` / `start write sdo tp codesys.` / `pack addr = {}.` / `sdo read,slave={},index={},subIndex={},value={}`

**真正的 SDO 由 CODESYS 执行**（libdataSvr 只解析、打包、转交）。

## 7. 已试过的 key/servoNum 组合（全部只让 SDOWRCount 计数，不触发 SDO）

| body | SDOWRCount | AllSDOWRInfo | sdo read 日志 |
|---|---|---|---|
| `{}` | — | 0 | 无 |
| `{"servoNum":6}` | — | 0 | 无 |
| `{"key":"J6"}` | — | 0 | 无 |
| `{"key":"J6","servoNum":6}` | — | 0 | 无 |
| `{"key":"H01.17","servoNum":6}` | — | 0 | 无 |
| `{"key":38,"servoNum":6}` | — | 0 | 无 |
| `{"key":"200117"/"200118"/"200101","servoNum":6}` | — | 0 | 无 |
| `{"body":[1 个]}` | **1** | 0 | 无 |
| `{"body":[3 个]}` | **3** | 0 | 无 |
| `{"body":[5 个]}` | **5** | 0 | 无 |
| `{"body":[2 个]}` | **2** | 0 | 无 |

**⇒ 信封（`{"body":[…]}`）一定正确（计数严格跟随元素个数）；
但元素内容从未被接受——`AllSDOWRInfo` 恒为 0、没有 `sdo read` 日志、
连服务端的 `the key {} is error.` 都没打印过，说明解析根本没走到 key 校验那一步。**

## 8. 下一步（按优先级）

1. **反汇编服务端 `DataSubProcess::readServoParams @0xf9cdd`**：看它拿到 `SDOWRCount` 之后的分支，
   以及为什么 `AllSDOWRInfo` 不填。（路线 A，本轮未做）
2. 反汇编 `parseAndReqGetServoParams @0xec03d` 的回调链（它用了 rapidjson，
   成员名与迭代顺序可从 `GetMember/FindMember` 的调用参数还原）。
3. 反汇编工具侧 `0x121050`（构造 `StructSettingsServoParams` 的函数），
   看结构里两个 QString 分别来自表格的哪一列。

## 8. 逆向环境要点（本轮沉淀）

- 维护工具 exe **带完整 COFF 符号表（19,561 个）**；**COFF 符号的 Value 是节内偏移，RVA = 节基址 + Value**（当成 RVA 用会全错）。
- 定位 xref 要用**指令边界扫描**；固定基址链接、无重定位表，直接搜 4 字节会大量假命中。
- `libdataSvr.so` 是 **Thumb**：符号地址为奇数，**capstone 必须传 `addr & ~1`**。
- 主控自带 `/mToolServer/tcpdump`；**EtherCAT 在 `eth0`**，机器人网在 `eth2`。
- `config/servoReadOnlyAddress.txt` = **`H01.17`**（厂商专门锁死的编码器位置角）。
