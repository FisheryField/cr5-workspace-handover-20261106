# 法兰实机脚本 · 连续运动逻辑升级（仿真 → 实机）报告

生成时间：2026-09-25（本机时区）
执行方式：**纯文件操作 + 纯静态校验**。全程**没有运行、也没有 import** A/B 两个脚本（它们会连真实机械臂）。

---

## 1. 本次做了什么

把 **A（仿真脚本）最新的“连续运动”逻辑整段搬进 B（法兰实机脚本）**：

| 角色 | 文件 | 行数 | md5 |
|---|---|---|---|
| A 逻辑来源（**只读，未改动**） | `D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂TCP仿真.py` | 1262 | `6523d32588385606527d4ff7d837ed46`（改前=改后） |
| B 原文件（备份） | `D:\mydata\workspace\机械臂法兰真实运动.bak_20260925_185818.py` | 1198 | `e613586127fbb2a76c724a78cc0a5540` |
| **B 新文件（结果）** | `D:\mydata\workspace\机械臂法兰真实运动.py` | **1462** | **`29863a4a791bdc06134d24794dbd68db`** |
| 站点目录副本 | `D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂法兰真实运动.py` | 1462 | `29863a4a791bdc06134d24794dbd68db`（与上面逐字节一致） |

坐标约定**没有变化**：操作员输入/显示/记录的仍是【法兰】位姿（不含工具）；法兰↔TCP 的换装仍然只发生在 B 的边界函数里。

### 拼接的三段源码（A 行号 → B 新文件位置）

| 段 | A 行号 | 内容 | 结果行数 |
|---|---|---|---|
| 常量 + 预检缓存 | 20-46 | `ALLOW_MOTION`、`MOVEJ_FALLBACK_MAX_DEVIATION_MM`、`_plan_cache`、`_cache_key_joints`、`_cache_key_pose`、`_movej_test_cached` | 27 |
| “连续运动”选项卡 GUI | 141-245 | `tab_traj` 整个选项卡（含导入/导出按钮、特异点选项、MoveJ 偏离输入框、`traj_log_output`/`traj_status_var`） | 105（B 新文件 1338-1442） |
| 连续运动函数块 | 447-1249 | `refresh_record_list` … `execute_recorded_trajectory`，共 **33 个顶层函数** | 803（B 新文件 333-1135） |

A 的 `log/set_status/get_input_values`（250-272）中**只吸收了 `log` 的写日志思路**（A 的 `log` 本来就同时写两个日志框），B 侧按第 4 节第 8 条把 B 自己的 `log(s)` 扩展成三处输出；`set_status`/`get_input_values` 属于单点运动，未搬（B 的单点页有自己的实现）。

---

## 2. B 侧保留不动（已字节比对，全部 OK）

| 区域 | 备份行号 | 字节数 |
|---|---|---|
| 模块 docstring | 1-19 | 1150 |
| imports | 21-27 | 166 |
| `ROBOT_SPEED = 20.0` / `NL` | 29-30 | 31 |
| **法兰边界函数 `_tool_mat` / `fanuc_to_pose` / `pose_to_fanuc` / `current_flange_pose`** | 34-59 | 979 |
| `robot = RDK.Item(...)` | 61-64 | 129 |
| 全局变量块 | 66-74 | 181 |
| `ensure_connected()`（含注释头） | 86-108 | 771 |
| 单点运动函数 `parse_points` … `execute_single` | 110-265 | 5210 |
| 目标关节运动函数 `_joint_values_from_entries` … `clear_joint_target` | 796-887 | 3359 |
| GUI 选项卡1 + 选项卡2 | 901-988 | 3962 |
| 日志区（`text_log`） | 1181-1186 | 266 |
| 启动日志（B 原有 6 行） | 1191-1196 | 715 |

另逐个函数做了 `ast.get_source_segment` 逐字节比对：`_tool_mat`、`fanuc_to_pose`、`pose_to_fanuc`、`current_flange_pose`、`ensure_connected` **全部逐字节相同**。

### 为接线而新增的内容（都是“接线”，不是算法）

1. `import itertools`（A 的函数块用到，B 原本没有）。
2. 名称适配（零改动转发，坐标数学完全没动）：
   ```python
   def fanuc_values_to_pose(x, y, z, rx, ry, rz):   return fanuc_to_pose(x, y, z, rx, ry, rz)
   def pose_to_fanuc_values(pose):                   return pose_to_fanuc(pose)
   ```
3. `simulation_running = False`（A 的 `execute_recorded_trajectory` 里有 `global simulation_running`，B 原本没有这个名字）。
4. `log(s)` 扩展成写三处（stdout + `text_log` + `traj_log_output` + `traj_status_var`），每处单独 try/except 兜住“GUI 还没建好”和 `root` 未定义。
5. `execute_trajectory()` 兼容壳保留，并**按 A 的参数签名改写**为 `execute_recorded_trajectory(trajectory_records, log)`（B 原壳是无参调用，A 的函数取参数，不改就会 TypeError；无其它代码调用它）。
6. 底部加了一条新的升级说明日志（原 6 行启动日志原样保留）。

---

## 3. 变换清单（共 50 项替换 / 53 处命中；每项都断言命中数，不符即中止）

### 3.1 仿真 → 实机（第 1-5 条）

| # | 变换 | 命中 |
|---|---|---|
| 1 | `RDK.setRunMode(RUNMODE_SIMULATE)` → `ensure_connected()` + `RDK.setRunMode(RUNMODE_RUN_ROBOT)`（A 的 `execute_recorded_trajectory`） | 1 |
| 2 | 其余 `RUNMODE_SIMULATE`（运行模式守卫）→ `RUNMODE_RUN_ROBOT` | **2** |
| 3 | `SIM_SPEED` → `ROBOT_SPEED`（B 的 `ROBOT_SPEED = 20.0` 保持不变，**没有用 50**） | 1 |
| 4 | `ALLOW_SIMULATION` → `ALLOW_MOTION`（常量块 1 + 函数块 1） | 1 + 1 |
| 5 | 在 `execute_recorded_trajectory` 的“已在运行/没有点”守卫之后、规划执行之前插入实机横幅日志 | 1 |

插入的横幅（原文）：

```python
    log('========== 实机连续运动：将在真实机械臂上执行，请确认工作空间无人无障碍 ==========')
```

### 3.2 措辞 仿真 → 实机（第 6 条，全部在函数块里，全部命中 1 次）

| 原（A） | 新 |
|---|---|
| `'障碍物预检仅允许在仿真模式执行。'` | `'障碍物预检仅允许在实机运行模式（RUNMODE_RUN_ROBOT）下执行。'` |
| `'_TCP仿真_路径预检'`（RoboDK 程序名） | `'_TCP实机_路径预检'` |
| `'_TCP仿真_整段碰撞复核'`（RoboDK 程序名） | `'_TCP实机_整段碰撞复核'` |
| `已有仿真正在运行，请等待结束。` | `已有运动正在运行，请等待结束。` |
| `当前禁止仿真或没有轨迹点。` | `当前禁止运动或没有轨迹点。` |
| `整段路径预检：{n}点（仿真模式）` | `…（实机模式）…` |
| `========== 正式仿真运动：…` | `========== 正式实机运动：…` |
| `运行模式改变，停止仿真。` | `运行模式改变，停止运动。` |
| `========== 连续运动仿真完成：…` | `========== 连续运动完成：…` |

拼接块里**已无任何用户可见的“仿真”字符串**（校验见第 5 节；仅剩 A 自带的 docstring 与新写的说明性注释/新启动日志）。

### 3.3 用户可见 TCP → 法兰（第 7 条：GUI 标签 + 描述“操作员自己那个点/这些点之间的直线”的日志/异常文本）

GUI 标签（A 141-245，10 项，含 1 项注释修正）：

| # | 原 | 新 | 命中 |
|---|---|---|---|
| 1 | `# 选项卡 2：连续运动（含导入导出）` | `# 选项卡 3：连续运动（含导入导出）`（B 里它是第 3 个选项卡） | 1 |
| 2 | `连续运动点输入：每次输入 1 个 TCP 点…` | `…1 个法兰位姿…` | 1 |
| 3 | 单选钮 `TCP（X,Y,Z,Rx,Ry,Rz）` | `法兰（X,Y,Z,Rx,Ry,Rz，不含工具）` | 1 |
| 4 | `标记当前 TCP 为末端特异点…` | `标记当前法兰位姿为末端特异点…` | 1 |
| 5 | `MoveJ兜底轨迹最大允许偏离TCP直线：` | `…偏离法兰直线：` | 1 |
| 6 | `读取当前TCP并写入` | `读取当前法兰并写入` | 1 |
| 7-9 | `普通 TCP 用 IK 判断可达…` / `标记为末端特异点的 TCP 跳过 IK` / `其后的普通 TCP 重新正常 IK。` | 三处 → `普通法兰点…` / `…的法兰位姿跳过 IK` / `其后的普通法兰点…` | 各 1 |
| 10 | `已检查通过的连续运动点（…可混合 TCP / 关节点）` | `…可混合 法兰位姿 / 关节点…` | 1 |

函数块内的用户可见文本（25 项，各 1 次，惟 `TCP IK：` 为 3 次）：

| 类别 | 原 → 新 |
|---|---|
| 记录列表标记 | `[TCP-特异点 J6优先…]` → `[法兰-特异点 J6优先…]`；`[TCP]   X=` → `[法兰]    X=`（保持列对齐；B 原来这里就写的是 `[法兰]`） |
| 记录/检查日志 | `[TCP-特异点]：已加入`→`[法兰-特异点]…`；`[TCP]：上一 TCP 点到当前 TCP 点…`→`[法兰]：上一法兰点到当前法兰点…`；`[TCP]：检查通过…`→`[法兰]…` |
| 输入点相关 | `末端特异点前一项必须是普通 TCP 点` / `必须与前一个普通 TCP 点相同。` / `不改变 TCP 位置。` / `该 TCP 点未加入轨迹。` → 全部改 `法兰点/法兰位置` |
| IK 日志 | `TCP IK：不可达 / 返回关节数量异常 / 可达`（3 次）+ `TCP IK 检查失败` → `法兰 IK：…`（**回到 B 原来的“法兰 IK”措辞**） |
| 连续段日志 | `的 TCP 连续 IK（n 个采样点）` → `的法兰连续 IK（…）`（B 原措辞）；采样点数值行 `TCP：X=…` → `法兰：X=…`（B 原措辞） |
| 预检异常 | `不匹配目标TCP。` / `特异点必须紧跟普通TCP点。` / `首个TCP没有限位内的逆解。`→`首个普通法兰点…` / `所标注TCP，请检查特异点标记/工具。`→`所标注法兰位姿…` / `首个TCP J6=`→`首个法兰点 J6=` |
| MoveJ 兜底偏离检查 | `允许最大TCP偏离` / `偏离TCP直线` / `t=… TCP=(…)` / `最大TCP偏离直线` / `最大偏离点TCP=` → 全部改 `法兰` |
| 读取当前位姿 | `读取当前 TCP -> 连续运动输入框` / `读取当前 TCP 失败：` → `读取当前法兰…` |

### 3.4 明确**没有**改的（第 7 条禁止清单 + 判定为“内部目标/非用户可见”）

- 内部记录类型字符串 `"type": "TCP"` / `'TCP'`、`rec['type'] == 'TCP'`、`item["type"] == "TCP"` 等全部保留。
- GUI 单选钮 `value="TCP"`、`traj_type.get() == "TCP"`、`traj_type.set("TCP")`、`_write_values_to_traj_entries(vals, "TCP")`（这是写给 `traj_type.get()` 的**取值**，不是显示文本）保留。
- JSON 字段名（`type`/`values`/`singular`/`j6_delta`）保留。
- 含 `tcp` 的函数/变量名一律保留：`_tcp_target_to_flange`、`_tcp_position_from_joints`、`_check_tcp_reachable`、`_check_tcp_segment_continuous`、`_check_movej_tcp_trajectory`、`first_tcp`、`tcp_count`、`tcp_defaults` 等。
- **A 的 docstring / 注释原样保留**（例如 `_check_tcp_reachable` 的 `"""检查单个 TCP 点 IK 是否可达…"""`、`_tcp_position_from_joints` 的 `"""关节角 -> 当前参考坐标系下的TCP位置…"""`、`_check_movej_tcp_trajectory` 的 docstring、`_retreat_orientation_records` 里的 `# 普通 TCP 与…`、A 常量块第 21 行注释里的“偏离TCP直线段”）。理由：第 7 条只授权改“用户可见”文本，注释/docstring 不属于；且“不要重构 A”。
- 两个 RoboDK 程序名只改了“仿真→实机”，`TCP` 部分未动：`_TCP实机_路径预检`、`_TCP实机_整段碰撞复核`。
- A 的 `_movej_test_cached` docstring 里“把仿真关节停在终点”一句**保留**（属 A 20-46 段，要求逐字保留；它是 docstring，不是用户可见文本）。

---

## 4. 逐字保留的证据（A vs 拼接结果，行级 diff）

| 段 | A 行数 | 结果行数 | 改动的 A 行 | 逐字相同的行 |
|---|---|---|---|---|
| 函数块 A 447-1249 → B 333-1135 | 803 | 803 | **43** | **760（94.6%）** |
| GUI 块 A 141-245 → B 1338-1442 | 105 | 105 | **8** | **97（92.4%）** |

改动的行全部是第 3 节列出的替换/插入项；**没有任何一行是算法、判定、顺序上的改动**。

---

## 5. 校验结果（全部通过）

1. **`py_compile`**
   - `D:\software\RoboDK\Python-Embedded\python.exe -m py_compile 机械臂法兰真实运动.py` → **exit 0**
   - `C:\Program Files\PyManager\python.exe -m py_compile …` → **exit 0**
2. **`ast.parse` + 报告**
   - `ast.parse` OK；文件 **1462 行**（脚本里 `count('\n')+1` 的报数写作 1463，因为文件以换行结尾；编辑器/read 工具显示 1462）。
   - `notebook.add` = **3**：`单点运动`（1251）、`目标关节运动`（1294）、`连续运动`（1342）。
   - 顶层函数 **65 个**（无重名）：A 块 33 个 + `_cache_key_joints`/`_cache_key_pose`/`_movej_test_cached` + B 原 20 个 + `fanuc_values_to_pose`/`pose_to_fanuc_values` + GUI 里的 8 个 `_xxx` 包装（`_read_current`、`_exec_joint`、`_update_traj_labels_and_defaults` 等）。
   - 顶层类：无。
3. **静态未定义名检查**：自写作用域感知的 AST 遍历（模块作用域 + 每个函数/lambda/推导式作用域，含 `global` 语义）。结果 **未定义名 = 0**。
   - 另把 `robodk.robolink` / `robodk.robomath` 的 `dir()`（319 个名字，**只 import robodk 库本身，没有 import A/B、没有 `Robolink()`、没有连接机器人**）导入检查：最终文件里“只能由星号导入提供”的名字共 **13 个**，全部命中 —— `COLLISION_ON/OFF`、`ITEM_TYPE_OBJECT/TOOL/ROBOT`、`RUNMODE_RUN_ROBOT`、`Fanuc_2_Pose`、`Pose_2_Fanuc`、`Robolink`、`eye`、`invH`、`norm`、`pose_angle`。
4. **拼接内容 / RUNMODE 证据**（A → B原 → B新）

   | 记号 | A | B 原 | B 新 |
   |---|---|---|---|
   | `RUNMODE_SIMULATE` | 5 | 0 | **0** |
   | `RUNMODE_RUN_ROBOT` | 0 | 6 | **11** |
   | `SIM_SPEED` | 4 | 0 | **0** |
   | `ALLOW_SIMULATION` | 3 | 0 | **0** |
   | `ALLOW_MOTION` | 0 | 0 | 3 |
   | `_plan_cache` | 16 | 0 | 16 |
   | `_cache_key_joints` / `_cache_key_pose` | 6 / 2 | 0 / 0 | 6 / 2 |
   | `_movej_test_cached` | 6 | 0 | 6 |
   | `MOVEJ_FALLBACK_MAX_DEVIATION_MM` | 3 | 0 | 3 |
   | `simulation_running` | 12 | 0 | 5 |
   | `itertools` | 2 | 0 | 2 |
   | `execute_recorded_trajectory` | 2 | 3 | 3 |

   - `ensure_connected()` 紧接 `RDK.setRunMode(RUNMODE_RUN_ROBOT)` 的子串存在：**True**；实机横幅存在：**True**。
   - 新文件中“仿真”字符串字面量只剩 2 处：A 的 `_movej_test_cached` docstring（逐字保留）与新加的启动说明日志（要求新增的那一行）。
5. **其它页与边界函数未变**：第 2 节的 12 段整段子串比对 + 5 个函数逐字节比对，**全部 OK**（`all_regions_unchanged=True`）。
6. 备份路径与 md5、最终文件 md5：见第 7 节。

---

## 6. 我**没有**做 / 需要你注意的地方（不确定项与风险）

1. **我没有运行、也没有 import B（或 A）**，所以“能连上机器人、能真的动”这件事**没有实证**；本次只做了语法与静态检查。
2. **`read_current_tcp_to_traj` 的语义提醒（A 的算法原样保留，未改）**：A 内用的是 `_trajectory_pose(robot.Joints()) = invH(PoseFrame)*SolveFK(q)*PoseTool()`，即 **带工具的 TCP 位姿**；而它写入的是“法兰输入框”。**若现场 RoboDK 里设置了非单位（非法兰）工具，这个按钮写进去的就是 TCP 数值而不是法兰数值**（B 原来的实现用的是 `current_flange_pose()`，是真法兰）。按“不改 A 算法、边界函数不动”的要求，我保留了 A 的写法，并把按钮/日志措辞统一成“法兰”。**现场用之前请确认工具是法兰（单位矩阵），或先核对一次读数。** 同类提醒：GUI 现在写“偏离法兰直线”，而该检查内部比较的是 TCP 位置（工具为单位矩阵时两者一致）。
3. **实机预检对 RoboDK 工位的依赖**：A 的预检要求工位里存在障碍物模型 `安装台_650x650x80mm`、`地面_禁止穿越`（`_enable_obstacle_checks` 缺模型会直接 `RuntimeError` 中止）。**实机工位若没有这两个模型，连续运动会被拒绝**——这是 A 的判定，我没有改。
4. **`robot.setJoints()` / `MoveJ_Test` / `MoveL_Test` / `Program.InstructionListJoints` 在 `RUNMODE_RUN_ROBOT` 下的行为**：A 的预检会用这些接口“试算并复位”机器人位姿。它们在 RoboDK 里属于测试/仿真接口，但**在 RUN_ROBOT 模式下是否会影响真实机械臂，我没有、也无法在不实机验证的情况下确认**。首次使用建议：清空工作空间、备好急停、只放 1~2 个相距很近的点试。
5. `execute_trajectory()` 兼容壳是我按 A 的签名改写的（B 原壳无参，直接保留会 TypeError）；除此之外没有任何 B 侧代码被我改动。
6. 拼接块里 A 的注释/docstring 里仍有 `TCP` 字样（内部术语），以及 A 常量块注释里的“偏离TCP直线段”“仿真关节”等字样——按第 7 条/第 6 条的授权范围（只改用户可见文本）保留。
7. 构建/校验脚本放在系统临时目录（`%TEMP%\flange_upgrade\`），**没有在 workspace 里留下额外文件**；除 B、B 的备份、站点目录副本和本报告外，没有改动任何其它文件（A 的 md5 前后一致）。

---

## 7. 回滚

```powershell
# 方式一：恢复备份（备份就是本次升级前的原文件，逐字节）
Copy-Item 'D:\mydata\workspace\机械臂法兰真实运动.bak_20260925_185818.py' `
          'D:\mydata\workspace\机械臂法兰真实运动.py' -Force
# 站点目录副本同样覆盖回去（如果已经拷过去了）
Copy-Item 'D:\mydata\workspace\机械臂法兰真实运动.py' `
          'D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂法兰真实运动.py' -Force
```

- 备份文件：`D:\mydata\workspace\机械臂法兰真实运动.bak_20260925_185818.py`
  （1198 行，md5 `e613586127fbb2a76c724a78cc0a5540`）
- 升级后文件：`D:\mydata\workspace\机械臂法兰真实运动.py`（1462 行，md5 `29863a4a791bdc06134d24794dbd68db`）
- 站点目录副本：`D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂法兰真实运动.py`（md5 同上，逐字节一致）

---

## 8. 追加改动：磨砂圆盘暂不参与碰撞判断（2026-09-25，本次）

> 上面第 1 节的 md5 是**本次追加改动之前**的。追加后以本节为准。

| 角色 | 文件 | 行数 | md5 |
|---|---|---|---|
| workspace 主文件 | `D:\mydata\workspace\机械臂法兰真实运动.py` | 1503 | `840f919687eeba1b3a914c18038e6731` |
| 站点目录副本（**源码同步＝LF**） | `D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂法兰真实运动.py` | 1503 | `840f919687eeba1b3a914c18038e6731`（逐字节一致） |
| RoboDK 运行副本（**CRLF**，文本内容同上） | `%TEMP%\机械臂法兰真实运动.py` | 1503 | `4fd7bcc7bde7baa385dd9fb89404a128` |

### 改了什么

工位里的 `磨砂圆柱_R180_H40`（即磨砂圆盘）**本阶段不参与碰撞判断**。注意这里是**显式关掉**而不是"不添加"——RoboDK 默认就会对工位内所有对象做碰撞检查，`_traj7_*.log` 里那条
`P15：MoveJ路径检查失败：门把手_bs1[连杆0] 与 磨砂圆柱_R180_H40[连杆0]` 就是它在拦路。

| # | 位置 | 内容 |
|---|---|---|
| 1 | 常量块（`MOVEJ_FALLBACK_MAX_DEVIATION_MM` 之后） | 新增 `EXCLUDED_COLLISION_KEYWORDS = ('磨砂',)` + 说明注释 |
| 2 | `_enable_obstacle_checks()` 之前 | 新增 `_disable_excluded_obstacle_collisions()`：按关键字匹配工位对象，把**机器人连杆 0~6** 与**所有工具**对它的配对全部 `setCollisionActivePair(COLLISION_OFF, …)`，返回被排除对象名 |
| 3 | `_enable_obstacle_checks()` 内 | 在 `RDK.setCollisionActive(COLLISION_ON)` **之后**调用它并写日志（顺序有意为之，见下） |
| 4 | 底部启动日志 | 新增一行提示当前排除关键字 |

- **只影响这一个对象**：安装台 / 地面的配对逻辑（原样保留在同一个函数里）不受影响。
- **恢复办法**：把常量改成 `EXCLUDED_COLLISION_KEYWORDS = ()` 即可，无需改其它代码。

### 为什么把排除放在 `setCollisionActive(COLLISION_ON)` 之后

读 RoboDK 5.9.0 的 API 源码确认：`setCollisionActive` 发的是 `Collision_SetState`（只有全局开关一个 int），
`setCollisionActivePair` 发的是 `Collision_SetPair`（对象对 + 连杆号 + 该对的状态），**两者是不同命令、互不覆盖**。
先开全局再关单对，语义最直观，也避免了"先关后开会不会被全局开关重置"的疑问。

### 现场实测（本次，只读探测 + 一次配对设置）

用 RoboDK 内嵌 python 对**当前打开的工作站**跑了一次探测
（`%TEMP%\probe_excl.py`，**没有设置任何关节、没有运动、没有保存工位**）：

```
robot valid: True Dobot CR5     RunMode: 6   (=RUNMODE_RUN_ROBOT)
before Collisions() = 0
matched objects: ['磨砂圆柱_R180_H40']
OFF robot-vs-磨砂圆柱_R180_H40:  link 0,1,2,3,4,5,6 -> 均为 1
OFF tool 门把手_bs1  vs 磨砂圆柱_R180_H40 -> 1
after  Collisions() = 0   CollisionPairs() = []
```

⇒ 8 个配对调用**全部返回 1**（成功），排除在真实工作站上生效。⚠️ 该探测**已经**改动当前会话的碰撞矩阵
（去掉磨砂圆盘的配对，**未保存**）；这与脚本每次预检都会做的事完全一致。要恢复就在 RoboDK 的碰撞矩阵里
把该对象的配对勾回来，或者不保存直接重开工作站即可丢弃这次改动。

⚠️ **当前工作站 `RunMode = 6`（RUN_ROBOT）** —— 也就是说这个工作站现在是**连着真机**的。
脚本的预检会调用 `robot.setJoints()` / `MoveJ_Test` / `InstructionListJoints`，在 RUN_ROBOT 下是否会动真机仍未确认
（见第 6 节第 4 条）⇒ 首次试跑请清空工作空间、手放急停、只放 1~2 个相邻点。

### 校验

- `py_compile`：PyManager 3.14.7 + RoboDK 内嵌 python **均 exit 0**；`ast.parse` OK。
- 关键字计数：`EXCLUDED_COLLISION_KEYWORDS` 9 处、`_disable_excluded_obstacle_collisions` 2 处（定义+调用）、`COLLISION_OFF` 4 处。
- 其它区域未动：连续运动逻辑（含 `_plan_cache` 16 处、`RUNMODE_RUN_ROBOT` 11 处）与三个选项卡均不变。
- 三份文件（workspace / 站点目录 / `%TEMP%` 运行副本）文本内容一致（运行副本为 CRLF，故 md5 不同属正常）。

### 自检：怎么确认 RoboDK 跑的是新版

启动后日志里应出现这一行（没有就是 RoboDK 里的 python 程序项还挂着旧代码，需要重新载入 .py）：

```
碰撞判断：工位对象名含【磨砂】的对象（当前=磨砂圆盘 磨砂圆柱_R180_H40）本阶段不参与碰撞判断；恢复办法见常量 EXCLUDED_COLLISION_KEYWORDS。
```

---

## 9. 现场报错 `IndexError: list index out of range` 的根因与修复（2026-09-25 夜，本次）

现场现象（用户实机跑 17 点轨迹）：

```
========== 整段路径预检：17点（实机模式） ==========
碰撞判断已排除：磨砂圆柱_R180_H40（本阶段的临时设置，见 EXCLUDED_COLLISION_KEYWORDS）
✕ 连续运动停止：已完成0点，阶段=路径预检；IndexError: list index out of range
```

**根因：整段预检被放在 RUN_ROBOT 模式下跑，而实机模式下 `robot.Joints()` 读不到真机。**

### 9.1 证据链（逐条可复现，全部只读）

| # | 证据 | 来源 |
|---|---|---|
| 1 | 实机模式下 `robot.Joints()` 返回 **`Mat(1,1) = [[0]]`**，且每次调用都打印 `WARNING: Robot connection failed timed out: Working...`（连测 3 次一致） | `%TEMP%\probe_joints.py` |
| 2 | `Mat.list()` 的实现是 `return self.tr().rows[0]`（"Returns the first column"）⇒ `[[0]].list()` = **`[0]`（只有 1 个元素）** | `robolink`/`robomath.py:1711` |
| 3 | 于是 `_plan_continuous_trajectory` 里 `saved = robot.Joints().list()[:6]` = `[0]`，`reference` 也只有 1 个元素 | 代码 |
| 4 | `_trajectory_start_candidates` 里 `nearest = [... for j, v in enumerate(q)]` 用到 **`reference[j]`**（j 到 5）⇒ **IndexError: list index out of range** | 代码（本次修复前 B 第 950 行） |
| 5 | 同一台工作站：`robot.SimulatorJoints()` → `[0.0]*6` 正常；`robot.ConnectedState()` → `(0, 'Ready')`；`robot.JointLimits()` → 6 元素正常 | 同上探测 |
| 6 | 仿真脚本能跑 轨迹7，是因为它在 `execute_recorded_trajectory` 里先 `RDK.setRunMode(RUNMODE_SIMULATE)` —— **仿真模式下 `Joints()` 不需要问驱动**，返回模型的 6 个关节 | A 代码 |
| 7 | 已验证的实机脚本 `机械臂TCP真实运动.py` **一次都没用过 `robot.Joints()`**（只用 `SimulatorJoints()`，并且有 `len(q) < 6` 的守卫）；升级前的法兰脚本只用过 1 次 | 计数 + 逐行读 |

⇒ 结论：不是 A 的算法错，而是**把"仿真模式专用的预检逻辑"整体搬到了实机模式**（第 1 节替换清单第 1 条），
触发了本环境一个已知不可靠的接口。

### 9.2 修复（5 处，全部在 B；A 仍未改动）

| # | 改动 |
|---|---|
| 1 | 新增 `_joints6()`：一律用 `SimulatorJoints()` 读当前关节，**读不到 6 个就抛明确的 RuntimeError**（不再让 IndexError 冒到上层）。全脚本 8 处 `robot.Joints().list()[:6]` + `current_flange_pose()` + `read_current_tcp_to_traj()` 全部改用它 |
| 2 | `execute_recorded_trajectory`：**整段预检改回仿真模式**（与 A 一致）—— `MoveJ_Test`/`MoveL_Test`/`InstructionListJoints`/`setJoints` 只动模型；**预检通过后才 `setRunMode(RUNMODE_RUN_ROBOT)` 执行真机** |
| 3 | `ensure_connected()` 的返回值**必须检查**（原来被忽略）；切回实机后再查一次 `ConnectedState()`，`status < 0` 就直接终止、不下发运动 |
| 4 | `_enable_obstacle_checks()` 的模式守卫从 `RUN_ROBOT` 改成 **`SIMULATE`**（自证"预检只动模型"这条约束，写错模式立刻报错） |
| 5 | 异常处理里**打印完整堆栈**并写入 `%TEMP%\法兰连续运动_异常.txt`（原来只打印一行 `类型: 消息`，堆栈丢了）；`finally` 里把运行模式恢复成 RUN_ROBOT |

### 9.3 修复后的实证（诊断脚本，只动模型）

用 `%TEMP%\diag_plan.py`（= B 的定义部分 + 一个只跑预检的 main；第一件事就是切 SIMULATE，
结束后恢复 RUN_ROBOT）对**同一个 `连续轨迹7.json`** 跑了一遍：

```
RunMode 进入前 = 6  →  已切到 = 1(SIMULATE)
导入点 = 11    展开点 = 17    起点关节 = [0,0,0,0,0,0]
碰撞判断已排除：磨砂圆柱_R180_H40
候选分支未通过：P15：J6 +180°超限，尝试其他转向组合。
整段路径预检通过：17点；首个法兰点 J6=-73.620°。
>>> 预检通过：17 点   （P1 MoveJ / P2 MoveL / P3 MoveJ兜底 / P4-P6 MoveL / P7 特异点 / … / P17 MoveJ兜底）
RunMode 已恢复 = 6
```

⇒ IndexError 消失，17 点**全部规划成功**，无回绕。脚本本身在真机上的执行仍未实测（需要用户现场跑）。

### 9.4 本次修复后仍未解决 / 需用户决定的两件事

1. **`robot.Joints()` 在本环境实机模式下不可用**（超时 → `[[0]]`）—— 所以脚本里"当前姿态"一律取 `SimulatorJoints()`，
   即 **RoboDK 模型姿态**。⇒ **执行前请确认 RoboDK 里模型的姿态与真机实际姿态一致**
   （连接正常时模型会跟真机同步；当前实测模型是 `[0,0,0,0,0,0]`，而真机不一定在全零位）。
2. **`连续轨迹7.json` 的坐标语义 —— 本文早先的判断已更正（2026-09-25 用户澄清）**：
   该文件当初是在**末端装法兰（工具≈0）** 的情况下跑出来的 ⇒ **它的数值就是法兰坐标**，
   本脚本按【法兰】解释**是正确的，不需要任何换算**。§9.3 诊断跑出的 17 点即该轨迹在法兰语义下的有效规划。
   - 两个脚本对同一份 JSON 的解释确实不同，但只在"工具有效"时才分叉：
     * A（仿真）：`fanuc_values_to_pose(v) = Fanuc_2_Pose(v)`（**不乘工具**）⇒ 把数值当 **TCP**；
     * B（法兰）：`fanuc_values_to_pose(v) = Fanuc_2_Pose(v) × PoseTool()` ⇒ 把数值当 **法兰**。
   - 两者的 IK 目标其实都是 `PoseFrame × Fanuc_2_Pose(values)`（工具在 `_tcp_target_to_flange` 里被除掉），
     **与工具无关** ⇒ **工具 = 法兰(≈0) 时 A 与 B 完全等价**；工具非 0 时 A 会把 TCP 摆到那些数上、法兰偏一个工具量。
   - ⚠️ 因此：**实物装什么，RoboDK 的 PoseTool 就要设成什么**。法兰路径本身不受工具影响，
     但**碰撞检查按工具模型算** —— 实物是法兰却挂着 159.629mm 抓手 = 偏保守；实物装了抓手却把工具设成 0 = **会漏检**。

### 9.5 本次修复后的文件

| 角色 | 文件 | 行数 | md5 |
|---|---|---|---|
| workspace 主文件 | `D:\mydata\workspace\机械臂法兰真实运动.py` | 1555 | `be55451916e8d212f5dfa7cc15379cdc` |
| 站点目录副本 | `D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂法兰真实运动.py` | 1555 | `be55451916e8d212f5dfa7cc15379cdc` |
| A（仿真脚本） | `…\RoboDK files 2\机械臂TCP仿真.py` | 1262 | `6523d32588385606527d4ff7d837ed46`（**未改动**） |

⚠️ **RoboDK 的运行副本 `%TEMP%\机械臂法兰真实运动.py` 是每次运行时才生成的、运行结束即删除**
⇒ **改了 .py 必须在 RoboDK 里重新载入这个脚本**，否则跑的还是程序项里那份旧代码。
自检：预检标题应显示 **`（仿真模式，只动模型）`**，并且启动日志里有 `碰撞判断：工位对象名含【磨砂】…`。


