# MEMORY_PENDING（workspace Memory 待写入快照 · 2026-10-12）

> 用途：2026-10-10~12 workspace Memory 服务端连续故障（宿主重启 / deadline 超时 ×2），supersede 五次尝试均未落盘，旧 Memory 仍停在 2026-09-28 固件时代。
> 2026-10-12 16:50 补记：memory_recall 已恢复可用（能取到旧 Memory cursor）；supersede 按用户指示推迟到明天，下文快照已刷成 v14n 版，届时直接照抄。
> 本文件 = 待写入内容的逐字快照。**服务恢复后**：memory_recall 取新 cursor → memory_change supersede 照抄下方分隔线以内内容 → 成功后删除本文件。
> 权威交接始终是工作区根 CHECKPOINT_v44.md；本文件只是 Memory 暂存草稿，不承载额外事实。

---

CR5 调试（D:\mydata\glm-workplace）状态 2026-10-12：主线=宏 sim_scripts\TCP真实运动_P2P版.py，现行 v14n-20261012-1712（=v14k 行为：细分步长回 20mm+事故注释）。**⛔ 2026-10-12 17:00 v14m(40mm) 实机判负：P5 细分第二跳 RoboDK 界面内机械臂与圆柱碰撞、运动停止，GUI 心跳与日志 17:00 同秒停更**；机理=40mm 跳弦误差叠加吃掉真裕度（轴线距199.9−半径R180≈19.9mm；落地时误把轴线距当裕度，算术错误已认领）；离线 verify 盲区：只验途经点在直线上，验不到 MoveJ 弦扫掠包络。**新铁律：细分步长永不得大于 20mm（实机双证：20mm 两度全过、40mm 一触即碰）；效率优化只许动非几何参数。** 处置：v14m .bak 留证，回滚 v14n 三连验证全绿、指纹回 v14k 基准（段 5/9=6/4），站内宏回读 v14n。方案定案不变：MoveL 只作路线图（细分+MoveJ），驱动 MOVL 永不可用（无工具补偿，4/4 全败：v10/v12b×2/v14l）；细分+MoveJ 4 战 4 胜（v13/v14j/v14k/v14k复跑）。v14l 永久拉黑（用户指示），源码 L960-961 防呆在位。待用户确认：实物是否接触、GUI 冻结 vs 闪退、安全移臂后再上机复验 v14n。E15 死因定论：主凶 v14d alt[5]-=2*delta（q-360°）、帮凶 v14f 枚举基准误用翻转后 target。两起使能事故定因（10-12）：①14:14 使能时机非法（m_powerFinish=false+dragMode=1→总线塌→下坠断电重启）；②14:35 0x86 回归（反馈弹跳+0s 强下使能）；homeEncoder 均无新写入。铁律：SSH 一律 tools/rssh.py 且复杂命令落 .sh；写盘须用户批准；使能/标零/实跑归用户；绝不保存工作站；ast.parse 先于 reswap；verify/刷新用嵌入式 python（系统 python 无 tkinter）；PS 内联嵌套引号必炸，一律落 .py；edit 前逐字重读。交接=工作区根 CHECKPOINT_v44.md + v14版本谱系与死点定位.html（含第 07/08 节）。旧基系警告仍有效：3.2.d.8 显示系≠旧定基系（92.24/18.10/155.73/-71.65/-143.48/-0.42），重标零后未重建 P1 則禁调旧基系点位。
