# SERVO_ZERO_FIX_README.md —— CR5 零点修理工具（纯主控侧）

> 工具：**`tools/servo_zero_fix.py`**
> 首次实证：2026-09-24 16:20~16:40，控制箱 `192.168.5.1`，伺服 J6 = `DS.3.1.5.0`。
> 结果：J6 上使能后从 `20.504629°` 变成 **`+0.000356°`**，且**整柜断电重启后仍然为 0**。

---

## 0. 一句话

**主控上报的关节角，取的是每轴 TxPDO 块的「最后一项」**，而那一项默认是 `0x6062`。
`0x6062` 在 `3.1.5.0` 上**一使能就变成编码器原始绝对计数**，所以每次上使能读数就"跑掉"。
`0x6064` 在**两版固件、使能/未使能四种组合下都是定基值**。

⇒ **把每轴 TxPDO 的末项从 `0x6062` 换成 `0x6064` 即可。** 这是**控制器上的 PLC 应用里每轴 2 个字节**的改动
（`0x6064` 与 `0x6062` 只差低字节），**伺服固件一个字都不用改**。

原理细节与全部证据见 `SERVO_SUMMARY.md` §16–§19。

---

## 1. 命令

```bash
# ① 看看某个 Application.app 的六张 TxPDO 表（离线，只读）
python tools/servo_zero_fix.py inspect data/cabinet/Application_allST.app

# ② 打补丁（★默认 dry-run；加 --write 才写文件）
#    --slaves all   = 六轴全打（六轴全是 3.1.5.0 时用这个）
#    --slaves 8     = 只打 slave 8 / J6
#    --slaves 3,4   = 指定从站
python tools/servo_zero_fix.py patch data/cabinet/Application_allST.app \
       --slaves all \
       --out data/cabinet/Application_fixed_all6.app \
       --crc-out data/cabinet/Application_fixed_all6.crc --write

# ③ 装到控制箱（先自动备份当前在用的变体，再上传）
python tools/servo_zero_fix.py install \
       data/cabinet/Application_fixed_all6.app \
       data/cabinet/Application_fixed_all6.crc

# ④ 从控制箱拉一份当前在用的应用下来（离线核对用）
python tools/servo_zero_fix.py pull --out data/cabinet/Application_live.app

# ⑤ 现场判据（只读）—— 关节角 / 每轴固件版本 / 每轴 PDO 末项
python tools/servo_zero_fix.py check

# ⑥ 回退（用最近一次备份）
python tools/servo_zero_fix.py rollback --yes
```

`--write` 之类写文件的操作都会打印改了哪些字节、并跑一遍断言闸门；
`install` / `rollback` / `check` / `pull` 需要控制箱在线（走工作区现成的 `rrun.cmd` / `rscp.cmd`）。

---

## 2. 工具内部做了什么（每轴 2 字节）

主控的 PDO 映射表**编在 PLC 应用里**，明文小端记录：

```
u16 0 | u32 (子索引<<16 | 索引) | u32 位长        ← 每条 10 字节
```

六张表 = slave 3..8 = J1..J6，条目数 `20/20/20/29/23/24`，
折算字节 `57/57/57/93/69/71` —— **与实测线上块长逐项一致**（工具里是硬断言）。
每张表的第 3 个条目是 `0x6064`，末条是 `0x6062`，两者都是 32 位
⇒ 对调后**表长不变、其后所有偏移不变**。

以六轴版为例（`data/cabinet/Application_allST.app`，md5 `8416cf0eee070a640702c077eb904b4e`）：

| 从站 | 轴 | `0x6064` 条目偏移 | 末条偏移 |
|---|---|---|---|
| 3 | J1 | `0xcbfd6` | `0xcc080` |
| 4 | J2 | `0xccf6c` | `0xcd016` |
| 5 | J3 | `0xcdf00` | `0xcdfaa` |
| 6 | J4 | `0xcf0be` | `0xcf1c2` |
| 7 | J5 | `0xd019e` | `0xd0266` |
| 8 | J6 | `0xd1268` | `0xd133a` |

**共 12 个字节**（每轴 2 个：把 `0x64` 和 `0x62` 对调）。
打完补丁的六轴版：md5 **`9a808cd9dd8f3aa6adaa4de1a34eb9b3`**。

`Application.crc` = CODESYS 包壳 + **`CRC32(Application.app)` 小端（偏移 4）**，工具会自动重算。

---

## 3. 最终验收 runbook（六轴全刷回 3.1.5.0 时）

```bash
# 1) 确认补丁已装（本工作区已经装好了六轴版；重装就是上面 ②③ 两条）
ssh root@192.168.5.1 "md5sum /dobot/userdata/codesys/allST/Application.app"
#    期望：9a808cd9dd8f3aa6adaa4de1a34eb9b3

# 2) 六轴刷回 CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin（照 FLASH_J6_20260924.md 的流程）

# 3) ★整柜断电重启（一次性同时让 FoE 固件生效 + 让新 PLC 应用生效；只重启控制器不够）

# 4) 上使能，然后跑判据
python tools/servo_zero_fix.py check
```

`check` 的期望输出：

```
2) per-axis servo firmware
   slave 3..8 / J1..J6 : 0x3150 = 3.1.5.0      （六轴都刷回去之后）
3) what the master mapped into 0x1A00 this boot
   address 1003..1008 : last=60640020   OK (0x6064 = re-based)
VERDICT: all servo axes read the re-based object 0x6064 -> zero should hold
```

以及第 1 段的六个关节角都应在 **|·| ≲ 0.5°**（残留量来自机械静止误差，不再是几十度）。

**再做一遍原始判据**：标定 → 下/上使能 → 等机械臂静止 ≥30 s → 记 V1 → 整柜断电 30 s → 上电 → 上使能 →
再等静止 → 记 V2，`|V1−V2|` 应 ≲ 0.05°。

---

## 4. ⚠️ 必须知道的

* ⚠️ **点动复核**：这个改动把每轴的**条目 2** 从 `0x6064` 换成了 `0x6062`
  （末项则相反）。已验证"上报关节角"这一条路是对的，但若 PLC 里还有变量绑在**条目 2** 上，
  它在 `3.1.5.0` 使能态下现在拿到的是原始计数。**请对每个轴点动/JOG 走一遍**，确认运动、限位、状态显示都正常。
  （唯一的实证是在 slave 8 上：上使能、保持、整柜断电重启都正常、无报警。）
* ⚠️ **工程下载 / 整机升级会覆盖这个补丁** —— 之后要重跑 ②③ 两步。
* ⚠️ 改的是**编译产物**，不是源码 ⇒ 无法只在某一次升级里"合并"，只能补丁后再装。
* ⚠️ `install` 会把**当前在用的变体**（由 `/tmp/codesysBoot` 决定，本机是
  `/dobot/userdata/codesys/allST/`）先备份到 `/dobot/userdata/codesys/BACKUP_pdo_<时间戳>/`。
* ✅ **原始基线**另存一份在控制箱：`/dobot/userdata/codesys/BACKUP_ORIGINAL/`（md5 `8416cf0eee070a640702c077eb904b4e`），
  回退到真·原版就用它：

```sh
cp -a /dobot/userdata/codesys/BACKUP_ORIGINAL/Application.app /dobot/userdata/codesys/allST/Application.app
cp -a /dobot/userdata/codesys/BACKUP_ORIGINAL/Application.crc /dobot/userdata/codesys/allST/Application.crc
reboot
```

* 📌 控制箱上一共 8 个 PLC 应用变体（`allST`(在用) / `allRX` / `StRx` / `RxSt` / `miniST` / `miniRX` / `Nova` / `MG`），
  由 `/dobot/bin/getVersion` 按 `codesys.json` 的 `(controlCab, 每从站 pid/rev)` 选一个，写进 `/tmp/codesysBoot`。
  本机选中 `allST`。换变体之后要重新打补丁。

---

## 5. 现场已有的成品

| 文件 | 说明 |
|---|---|
| `data/cabinet/Application_allST.app` | **真·原版**（md5 `8416cf0eee070a640702c077eb904b4e`） |
| `data/cabinet/Application_fixed_all6.app` / `.crc` | **六轴补丁版**（md5 `9a808cd9dd8f3aa6adaa4de1a34eb9b3`）—— 已装到控制箱 |
| `data/cabinet/Application_allST_patched.app` / `.crc` | 早期只补 slave 8 的版本（留档） |
| `data/cabinet/mem_73000000_afterB_enabled.bin` | 补丁生效后的主控 PDO 映像转储（使能态） |
| `data/cabinet/SDO_AFTER_B.txt` | 同期的 SDO 读回（`0x6062` vs `0x6064`） |
| `/dobot/userdata/codesys/BACKUP_ORIGINAL/` | 控制箱上的真·原版基线 |
| `/dobot/userdata/codesys/BACKUP_pdo_*/` | `install` 每次自动备份 |

---

## 6. 现场验收记录（2026-09-24 晚，六轴全刷回 3.1.5.0 之后）

时间线（mToolServer.log + homeEncoder.json + uptime 反推）：

- 16:38–16:40 六轴全部刷回原版 `3.1.5.0`（slave 8→7→6→5→4→3，全部 `errcode=0`），~16:44 重启。
- 17:03–17:20 用户四次清除标定 → **17:53:43 成功标定**（jointHomeState 全 true）→ ~17:55 再次重启。
- 当日 `logServoError` = 0 条。

`check` 实测（~19:03）：

- 六轴 `0x5000:07` 全部 `0x3150 = 3.1.5.0`；
- 六轴 `0x1A00` 末条全部 `60640020 OK`（entries=14/14/14/1D/17/18）—— 本次开机补丁映射已生效；
- 关节角：J1=+3.125°, J2=+0.418°, J3=−0.339°, J4=+0.008°, J5=−2.631°, J6=+180.000000°。
  J6 为用户点动所致（用户已确认）；J1–J5 读数成因未判定（可能仅机械摆放位姿），**待 §19.4 复验时一并观察**。
- 线上 `/dobot/userdata/codesys/allST/Application.app` md5 = `9a808cd9dd8f3aa6adaa4de1a34eb9b3`（六轴补丁版）。

**仍未做的验收（下一步，见 SERVO_SUMMARY.md §19.4）**：
① 下使能→重新上使能，读数应仍 ≈0；② 整柜断电重启→上使能，应仍 ≈0；
③ **六轴 JOG 复核**（补丁把每轴条目 2 换成了 `0x6062`，需确认没有别的变量绑在条目 2 上出问题）。

> 工具备注（2026-09-24）：本机 `ssh.exe` 损坏后，`servo_zero_fix.py` 传输层已改为 **paramiko 优先**
> （`rrun.cmd`/`rscp.cmd` 回退保留），凭据运行时解析自 `.askpass.cmd`，命令用法不变。
