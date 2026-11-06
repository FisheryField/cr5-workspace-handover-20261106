# 末端作业时避免碰撞误报的方案（CR5 · 固件 3.1.5.0 · 主控 3.5.6.1）

> 归档时间：2026-09-28 ｜ 场景：**末端在作业中会顶到工件/夹具（期望的"硬接触"），不希望因此报警停机**
> 所有接口与配置项均来自**本机实测**（`gcontrol` / `libdataSvr.so` 符号 + 控制器上的配置文件）✓

---

## 0. 先划一条红线 ⛔

`/dobot/userdata/CR5_sys_files/project/settings/function/collisionDect.json` 里有总开关：

```json
{ "level": 2, "mode": 3, "backDistance": 10, "value": true }
```

* **`"value": true` 是碰撞检测总开关** ⇒ **改成 `false` 就是彻底关掉** ✗
* **⇒ 绝对不要关** ✗ —— 关掉后机械臂对**任何**碰撞都不再有反应（撞坏工件、夹具、甚至伤人）✓
* **本方案的全部目的**：**在保留"大幅碰撞保护"的前提下，让"作业中期望的硬接触"不再触发停机** ✓

---

## 1. 误报的两个根因（先消除它们，成本最低、收益最大 ✓）

### 1.1 负载参数（★ 第一嫌疑 ✗）

```
现状: /dobot/userdata/CR5_sys_files/project/settings/function/loadParams.json
      { "centerX": 0, "centerY": 0, "centerZ": 0, "loadValue": 0.2 }
                                              ↑ 只有 0.2 kg，重心在法兰原点
```

**机理**：控制器的碰撞判据建立在**动力学模型**上。若工具的**真实重量/重心**与设定不符，
则作业时的正常作用力会被模型解释成"外力冲击" ⇒ **误报碰撞** ✗

**做法**（任一）：
| 途径 | 操作 |
|---|---|
| **示教器 / DobotStudio**（推荐 ✓） | 设置 **工具重量(kg)** 与 **重心(mm, 相对法兰)**；多数版本有"负载辨识"向导 |
| **API** | `SetLoad(weight, cx, cy, cz)`（符号：`SetLoadParam(tagLoadParams*, int)`） |

**验证**：改完后 `loadParams.json` 的 `loadValue`/`center*` 应随之更新 ✓

### 1.2 工具坐标系（TCP）精度

TCP 标定不准 ⇒ 力矩/位姿换算带偏差 ⇒ 也会抬高误报率 ✓
**做法**：确认 `PoseTool()` 与真实工具一致（尤其**重量集中点**与**重心**）✓

---

## 2. 碰撞判据的**灵敏度分级**（保留保护、只放宽门槛 ✓）

### 2.1 `collisionDect.json` 的五档阈值

数值**越大越不敏感** ✓（前三个值对应 J1~J3，后三个对应 J4~J6）：

| 等级 | J1 | J2 | J3 | J4 | J5 | J6 |
|---|---|---|---|---|---|---|
| **Level1（最宽松 ✓）** | **101.0** | **101.0** | **101.0** | **15.15** | **15.15** | **15.15** |
| **Level2（当前 ✗）** | 30.0 | 51.0 | 30.0 | 10.0 | 10.0 | 10.0 |
| Level3 | 25.0 | 45.0 | 25.0 | 8.0 | 8.0 | 8.0 |
| Level4 | 22.5 | 37.5 | 22.5 | 7.0 | 7.0 | 7.0 |
| Level5（最敏感） | 20.0 | 30.0 | 20.0 | 5.0 | 5.0 | 5.0 |

**其它字段**：
* **`"mode": 3`** —— 碰撞模式（配合 `SetCollisionMode(short,int)` 使用，语义待实测确认 ✓）
* **`"backDistance": 10`** —— 碰撞后**回退距离(mm)**；作业中若希望"顶住就停住不后退"，此项可设 0 ✓

**做法**：`level` 由 **2 → 1** ✓（阈值放宽到 101/101/101 + 15.15）
**⇒ 效果**：正常作业的力不再触发；**大幅碰撞仍会被拦** ✓

### 2.2 `AdvancedFunction.json` 里的碰撞三项（**当前值已记录** ✓）

```json
"CollisionPosErrorThreshold": [1, 1, 1, 1, 1, 1],           ← 位置误差阈值（mm 级）
"CollisionVelErrorThreshold": [30, 30, 30, 30, 30, 30],     ← 速度误差阈值
"AfterColliisonTorqueLimitSwitch": true                     ← ★ "碰撞后力矩限制开关"
```

**`AfterColliisonTorqueLimitSwitch`** 是本次方案的关键未知项：
* 名字直译 = **"碰撞后是否切换力矩限制"** ⇒ 很可能控制"碰撞后**继续限力运行** 还是 **立即停机**" ✓
* **它当前是 `true`** ⇒ 若要试改成 `false`，**必须先做单轴低风险试验**（见 §6）✗

### 2.3 `generalSafeSetting.json`（安全约束，一般不动 ✓）

```json
{ "safeconfig": { "forceConstr": 65, "powerConstr": 12, "velConstr": 14, "monentumConstr": 15 } }
```
**⇒ 这是协作安全的标准约束，除非有明确依据，不建议改** ✗

---

## 3. ★ 碰撞后的**行为**：让它"柔顺"而不是"急停"（最贴合你的场景 ✓）

从符号表解出的接口：

| 接口 | 签名（解自符号） | 推测语义 |
|---|---|---|
| **`SetCollideDrag`** | `(char)` | **碰撞后进入"拖拽/柔顺"状态**（而非急停下使能）—— ★ **最可能正是你要的** |
| `SetCollisionModeEhi` | `(short, int)` | 碰撞**模式**选择（例如：停止 / 回退 / 柔顺 三种行为）|
| `SetCollisionLevelEib` | `(int, bool)` | 等级 + 一个布尔（可能是"是否记录日志/是否启用"）|
| `SetCollisionLogEib` | `(int, bool)` | 碰撞日志开关 ⇒ **调试期打开，便于定位误报** ✓ |

**⇒ 推荐实施顺序**：
```
① 先打开碰撞日志（SetCollisionLog）—— 这样每次触发都能留下证据
② 用 SetCollisionMode 试着切换"碰撞后行为"，观察作业中是否变成"顶住不走 / 柔顺跟随"
③ 若 SetCollideDrag 可单独开启 ⇒ 它是"作业中允许被顶住"的正解 ✓
```
⚠️ **这三个接口的取值域未实测** —— 建议**先在 DobotStudio 里找"碰撞设置/碰撞后行为"界面**（界面背后就是这几个接口 ✓，比盲试安全 ✓）

---

## 4. 接触前预防：电子皮肤（若有硬件则最安全 ✓）

```
开关: /dobot/userdata/CR5_sys_files/project/settings/function/elecSkin.json   = {"value": false}  ← 当前关闭
参数: .../settings/function/elecSkinParams.json = {"mode":2,"avoidDistance":80,"avoidVel":100,...}
配置目录: /dobot/userdata/project/process/elecSkin/
           ├── switch.json        开关
           ├── sensitivity.json   灵敏度
           ├── avoidParams.json   避让参数（距离/速度/加速度）
           ├── jointLimit.json    关节限位
           └── default.json       默认值
```

**⇒ 电子皮肤能在**接触之前**就减速/停止** ✓ ⇒ **⇒ 比"调低碰撞门槛"更安全 ✓**（代价：需要硬件 + 会牺牲一点作业力 ✓）

---

## 5. 工程/机械侧（从源头减小碰撞力 ✓）

| 做法 | 说明 |
|---|---|
| **柔性工装 / 弹簧缓冲 / 浮动接头** | 让末端在接触瞬间"让一下"，作用力峰值大幅下降 ✓ |
| **力控 / 柔性伺服（若控制器支持）** | 直接以目标力闭环，而不是位置硬顶 ✓ |
| **作业姿态优化** | 让"顶住"的方向尽量**顺着重力/顺着大臂**，减小关节力矩突变 ✓ |
| **降低接触瞬间的速度** | 接触段用低速接近（`SpeedFactor` 局部降低），碰撞判据更难被触发 ✓ |

**⇒ 与我们已有的 `test.py` 结合**：接触段可单独给一个低 `ROBOT_SPEED` ✓

---

## 6. 实施与验证路线（建议按顺序，每步都可回退 ✓）

| 步 | 动作 | 风险 | 验证判据 |
|---|---|---|---|
| **0** | **备份** `collisionDect.json` / `AdvancedFunction.json` / `loadParams.json` | 无 | 备份文件存在 ✓ |
| **1** | **修正负载重量与重心**（示教器或 `SetLoad`） | 无 | `loadParams.json` 更新 ✓；作业误报明显减少 ✓ |
| **2** | **打开碰撞日志**（`SetCollisionLog`，或用界面的"碰撞记录"） | 无 | 每次触发都有记录 ✓ |
| **3** | **`collisionDect.json` 的 `level`：2 → 1** | 低（仍保留大幅碰撞保护 ✓） | 作业中不再误报；人为轻撞仍能触发 ✓ |
| **4** | **在界面上调"碰撞后行为"**（背后是 `SetCollisionMode` / `SetCollideDrag`） | 中（语义需实测 ✓） | 顶住时"柔顺/停住"而不是急停下坠 ✓ |
| **5** | 若仍不够 ⇒ **试 `AfterColliisonTorqueLimitSwitch` 改 false** | 中高（会让碰撞后继续出力 ✗） | 必须**先单轴、低速、小范围**试验 ✓ |
| **6** | 工程侧加**柔性工装/力控** | 需硬件 | 从源头消除 ✓ |

---

## 7. 一句话总结

> **不要关碰撞检测**（`value:false`）✗；
> **先修负载参数（`SetLoad`）**✓ —— 这是"误报"最常见的真凶；
> **再把碰撞等级从 2 降到 1**✓ —— 放宽门槛但保留保护；
> **真正对症的是"碰撞后行为"**✓（`SetCollideDrag` / `SetCollisionMode`）—— 让它顶住时**柔顺/停住**而不是**急停下使能**；
> **有条件就上电子皮肤**✓（接触前减速，最安全）。

---

## 附：本方案引用的全部接口签名（解自 `gcontrol` / `libdataSvr.so` 符号）

```
SetCollisionLevel(int, bool)              SetCollisionMode(short, int)
SetCollisionLevelERKSt / SetCollisionLevelEib / SetCollisionLogEib
SetCollideDrag(char)                      SetCollideDragERKSt / SetCollideDragEc
SetLoad(...) / SetLoadERKSt / SetLoadParam(tagLoadParams*, int) / loadSet(_stLoadParams*, bool)
GetLoadParam() / GetFCLoadIDEi / GetLoadParamEv
SetSafeSkin(...) / SetSafeSkinCmd(short, bool) / SetSafeSkinERKSt / SetResetSkinCmdEv
SetDragSenseParams(DragSenseAdjust*, bool) / SetDragTeachEnabledEc / SetDragTeachModeEc
```

**相关文件**
| 文件 | 内容 |
|---|---|
| `settings/function/collisionDect.json` | 碰撞 5 档阈值 + level/mode/backDistance/value |
| `settings/function/loadParams.json` | 负载重量与重心 |
| `settings/function/generalSafeSetting.json` | 协作安全约束 |
| `settings/function/elecSkin(Params).json` | 电子皮肤开关与参数 |
| `properties/AdvancedFunction.json` | `CollisionPosErrorThreshold` / `CollisionVelErrorThreshold` / `AfterColliisonTorqueLimitSwitch` |
| `process/elecSkin/*.json` | 电子皮肤细则（switch/sensitivity/avoidParams/jointLimit/default） |
