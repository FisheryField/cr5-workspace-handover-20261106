# RoboDK 末端轨迹显示：红绿蓝小坐标轴（FrameSizesPath）

> 2026-09-25 现场定位。对象：本机 RoboDK v5.9.0.25042（`D:\software\RoboDK`）。

## 症状

RoboDK 里机器人的末端运动轨迹看起来是「**黄色曲线 + 沿曲线垂直方向的红/绿/蓝小线段**」，
而不是 RoboDK 默认的单色曲线。

## 根因

**RoboDK 会在"路径"的每个点上绘制一个坐标系**（X 红 / Y 绿 / Z 蓝），
尺寸由命令 **`FrameSizesPath`** 控制，**默认 150 mm**。
轨迹是一条密集采样曲线 ⇒ 这些 150 mm 的三色坐标轴连成一串，
看起来就像"曲线上到处插着红绿蓝小线段"。

验证（API，只读+显示类）：

```
RDK.Command('FrameSizesPath')        -> '150'                     # 原值
RDK.Command('FrameSizes')            -> '350;250;150;100;30'      # 第三项就是它
RDK.Command('FrameSizesPath','0')    -> 'OK'
RDK.Command('FrameSizes')            -> '350;250;0;100;30'
```

设为 0 后操作员目视确认：**"只有单色曲线"** ✓（就是目标状态）。

## 修法（已落地）

1. **当次会话**：`RDK.Command('FrameSizesPath', '0')` —— 立即生效 ✓
2. **固化**：该值是**会话级**的（不写进 `%APPDATA%\RoboDK\settings.ini`，重启会丢）⇒
   已在使用方脚本 `机械臂TCP仿真.py` 里 `RDK = Robolink()` 之后加：

   ```python
   try:
       RDK.Command('FrameSizesPath', '0')
   except Exception:
       pass
   ```

   （同一份内容已同步到它实际运行的副本 `%LOCALAPPDATA%\Temp\TCP仿真8.py`，下次启动即生效。）
3. 可选：RoboDK 快捷方式加命令行参数 `-FrameSizesPath=0`，覆盖"手动启动 RoboDK"的情况
   （RoboDK 支持把任意 `Command()` 名以 `-名字=值` 形式当启动参数）。

## 排除项（都不是原因，别重复试）

- `Trace_Render_Style`（0/1/2/3）—— 逐值让操作员目视，**都不是**原因；
  它只影响轨迹自身的渲染样式，不影响那些坐标轴。
- `RDK.Command('Trace', ...)` —— 命令表原文只有 **`On|Off|Reset`**（无样式/颜色参数）。
- `SpindleOn(color)` / `Spray_Add(..., COLOR=...)` —— 那是**另一套**机制（喷迹），
  每次调用会**追加**一条该颜色的喷迹（`COLOR_LIST` = 白/红/绿/蓝/青/品红）⇒
  多次调用会叠出多色轨迹；本次不是它。
- 站里 12 个 `TCP轨迹/TCP仿真_...` 点云对象 —— 不是它们（改色/隐藏都对画面无影响）。

## 工具

`tools/robodk_framesize_fix.py`（画一段仿真轨迹 + 四选一对话框确认）、
`tools/robodk_commands_dump.py`（导出 RoboDK 自报的命令表 `RDK.Command("","")`）、
`tools/robodk_station_items.py`（列站内对象/颜色/可见性）、
`tools/robodk_trace_query.py`。
