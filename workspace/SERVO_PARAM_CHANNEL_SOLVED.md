# 伺服参数通道 —— 已破解（2026-09-23/24）

> 本文件是 `SERVO_PARAM_CHANNEL.md` 的最终结论页。上一版停在"请求返回 {\"status\":true} 但
> `AllSDOWRInfo` 不填充、日志无 `sdo read`"，本篇把那条链路**从 HTTP 一路解到总线邮箱**，结论是：
> **协议完全解开了，但这条通道在本机从来没工作过。**

## 1. 决定性工具：`libdataSvr.so` 的 PLT 表已解开

- `.rel.plt` 2933 项，`.plt` 35816 B。桩**不是均匀栅格**：2781 个 12 字节（纯 ARM）、150 个 16 字节（带 `bx pc; nop` 的 Thumb 互通桩）。
- 做法：在 `.plt` 内按 2 字节对齐扫 `add ip,pc,#imm` / `add ip,ip,#imm` / `ldr pc,[ip,#imm]!` 三连，
  算出 GOT 槽再回查 `.rel.plt`。**2932/2933 命中**，结果存 `tools/plt_map.json`。
- 脚本：`tools/plt_scan.py`。

### ⚠\. symtab 的 `Value` 是**绝对地址**，不要再加 section 基址
`parseAndReqGetServoParams` 的 `Value=0xec03d` 直接就是绝对地址（加 `.text` 基址 0xbc7f0 得到 0x1a882d，是错的）。
踩过一次坑：按 0x1a81fc 反汇编 `readSDO` 得到的是完全无关的 JSON 解析代码。

## 2. HTTP 协议完全解开

**端点**：`POST http://192.168.5.1:22000/settings/readServoParams`（**无需认证**）

```json
{"body":[{"key":"addr200117","servoNum":"J6"}]}
```

| 字段 | 规则 | 证据 |
|---|---|---|
| `servoNum` | **必须字符串 `"J1"`…`"J6"`**，数字直接类型检查失败 | 反汇编 0xec218/0xec284/0xec2c8/0xec2e0/0xec35c/0xec37c 六处 `std::string::compare` 比 J1..J6，命中后写入 `3-r3…8-r3`＝**EtherCAT 站号 3~8**；日志 `sdo read,slave=8` 对应 J6 ✓ |
| `key` | `"addr" + hex(0x2000+H组号) + 两位十进制(子索引)` | `addr200117` → 日志 `index=8193(0x2001),subIndex=17` 且**无** `the key … is error.`；`H01.17`/`200117`/`2001.17` 全部被重建为 `addr000` |

```
POST {"body":[{"key":"addr200117","servoNum":"J6"}]}
→ 200 {"status":true}
GET  → {"body":[{"servoNum":"J6","key":"addr200117","status":false,"value":0}],"status":true}
```

**key 格式由这两条日志唯一确定**：
```
[k] the key H01.17 is error.          ← 解析失败，index/sub 归 0
[✓] start read sdo from codesys.
[✓] sdo read,slave=8,index=8193,subIndex=17,value=0.   ← 没有 fail 行
```

## 3. `parseAndReqGetServoParams`（0xec03c, 1080 B）控制流

1. `HasMember("body")` → 必须是 **array**（`ldrh [r0,#0xe]; cmp #4`）。
2. `r2 = [array]`（元素个数）→ `cmp #0x12c0(=4800)` 截断 → 存入 GOT 全局 `SDOWRCount`。
   （`AllSDOWRInfo` = 115200 B ÷ 4800 = **每条 24 B** ✓，与观测到的 `SDOWRCount=2` 吻合）
3. 逐元素（16 B 一个 rapidjson `GenericValue`）：取 `"key"`（必须 string）、`"servoNum"`（必须 string）。
4. `servoNum` 六选一命中 → `SDOInfo[0] = 站号`；`GetIndexFromAddr(key, &SDOInfo[4], &SDOInfo[8])` 出 index/sub；
   `SDOInfo[20] = 1`。
   **没命中 → `AllSDOWRInfo[i]=0` 并整请求返回 −1**（0xec38a）。
5. `AllSDOWRStatus = 1`（读取中）→ 对每条调 `readSDO(this, SDOInfo&, 250000)`（=250 ms 超时）→ `AllSDOWRStatus = 3`。

**SDOInfo 布局**：`+0`站号 `+4`index `+8`subIndex `+0xc`value `+0x14`有效标志（共 24 B）。

## 4. ★ 失败点：CODESYS 从不服务那块共享内存邮箱

`DataSubProcess::readSDO`（**0xeba0c**, 232 B）：

```
if (this == 0) return -1
st = *(this + 0xe20)                      // 共享内存/状态块
if (st->[0x4c4] != 3 && st->[0x4c4] != 6) return -1      // 入口门禁
log("sdo read,slave=%d,index=%d,sub=%d,val=%d")          // #4613
st->[0x4c8]=slave; st->[0x4cc]=index; st->[0x4d0]=sub
st->[0x4c4] = 1                            // 写请求
usleep(250000)
if (st->[0x4c4] != 3) return -1            // ← 失败在这里（无日志）
value = st->[0x4d4]; valid = (st->[0x4dc]==1); return 0
```

- `libdataSvr.so` 由 **`codesyscontrol` (pid 374) 加载**；22000 端口也属于 pid 374。
  即这块邮箱是 **DataSvr ↔ CODESYS PLC 应用**的数据交换区。
- 实测：写请求后连续轮询 5 秒，`[0x4c4]` 永远不回到 3。
- **全日志历史（522,607 行）里 `sdo read,slave` 仅出现 9 次，全部是本会话 16:53 之后的探测**
  ⇒ 这个功能在本机**从未被成功使用过**。
- 所有读（H00/H01 组 × J1/J6，共 40+ 次）返回 `status:false, value:0`。

## 5. `mToolServer` 也没有这条路

`/mToolServer/mToolServer`（2,302,802 B，已存 `data/mToolServer.bin`）用 SOEM（`ethercatcoe.c`）+ libevent evhttp。
全部 `HttpServer` 处理器只有：

`updateFunc_CRSingleFwAndXml / CRAllFwAndXml / singleStatus / CRAllStatus / getActualXmlVersion /
checkKernelVersion / checkPartitionOccupancy / updateKernel / diskCheck`、`protocolFunc_getVersion`、
`faultFunc_check / faultFunc_repair`、`checkFiles / checkDNS / checkMAC / syncTime / repairOverTurn /
repairDefaultIp / repairDNS / repairMAC`。

**没有任何伺服参数/SDO 端点** —— 它链 SOEM 的 CoE 只是为 FoE 固件下载服务。

## 6. 总线层：两版固件下控制器做的事**逐字节相同**

重新解了 codex 的两次抓包（`data/codex_b/ethercat_pcap/`）：

| 抓包 | 总帧 | 非周期帧 | 邮箱交换 |
|---|---|---|---|
| `zero32_calibration.pcap`（3.2.D.8） | 73042 | 48 | 有 |
| `capture315_ethercat.pcap0`（3.1.5.0） | 56788 | **0** | 无（该窗口没标定） |
| `capture315_ethercat.pcap1`（3.1.5.0） | 28898 | 48 | 有 |

两组 48 帧的载荷**逐字节相同**。每站一次的邮箱事务是：

```
请求 (FPWR st=0x03eb…0x03f0 ado=0x1800):  00 20 | 40 | 7c 60 | 00 | 00000000
响应 (FPRD st=0x03eb…0x03f0 ado=0x1a30):  00 30 | 43 | 7c 60 | 00 | 00000000
```

`40`=CoE SDO Upload Request，`43`=带 4 字节数据的 Upload Response，
对象 **`0x607C:00 Home offset`**，六站**全部返回 0**。之后跟随 OD 名称表枚举（帧里可见 ASCII
`"Velocity Actual Value"`）。**控制器只读不写 0x607C。**

⇒ 与 `ZERO_CHANNEL_3.2.D.8.md` 独立互证；
⇒ 再次确认：**控制器对两版伺服发的命令完全相同，差异 100% 在驱动器内部。**

## 7. 结论与下一步

- ~~"控制器没有零点持久化路径"~~ ✅ 成立（本篇再次独立验证）。
- ~~"伺服参数通道可以读回零点对象"~~ ❌ **本机不可用**：CODESYS 侧不服务邮箱，mToolServer 无端点。
- ⇒ **唯一剩下的路是自己在控制器上接管 eth0，用 SOEM 直接读写驱动器对象字典**
  （即 `Dobot_CR5_主控文件说明.md` §615 的**方案 D**）。这条路上个会话**已经验证可行**：
  codex 的 `ecat_zero` 曾成功写出 `0x607C`（wkc=1）。
- **下一次实验（决定性）**：本机现在是 **J1–J5 = 3.2.D.8、J6 = 3.1.5.0** 的混合状态——
  同一台机器上的天然 A/B。用 `ecat_zero` 逐对象 dump **J6 与 J1 的厂商对象（0x5001~0x5007 及全 OD）并 diff**，
  差异项就是"3.2.D.8 会写、3.1.5.0 不写"的那个零点对象。
  ⚠ 风险：短暂接管 eth0 会让 CODESYS 报总线错误，机器人必须先下使能。

## 8. 本次新增脚本

`tools/plt_scan.py`（PLT→符号）、`tools/dis_get3.py` + `tools/resolve_get.py`（`parseAndReqGetServoParams` 带符号反汇编）、
`tools/dis_real.py`（按 symtab 绝对地址反汇编 + PLT/字符串/GOT 注释）、`tools/mb_scan.py` / `tools/mb_diff.py`（邮箱帧解码与两版 diff）、
`tools/mtool_strs.py` / `tools/mtool_routes.py`（mToolServer 端点清查）、`tools/findline.py`（用 `__LINE__` 立即数定位函数）。
