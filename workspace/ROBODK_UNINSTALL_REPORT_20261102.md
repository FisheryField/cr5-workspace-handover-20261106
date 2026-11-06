# RoboDK 卸载记录（2026-11-02）

## 结果

- 卸载方式：官方 `RoboDK uninstall.exe /S`（RoboDK 5.9.0，NSIS），管理员权限执行，退出码 0。
- 安装目录：`D:\software\RoboDK`（约 1.6 GB / 19,907 文件）已删除。
- 快捷方式：开始菜单 `RoboDK` 文件夹、公共桌面 `RoboDK.lnk` 已删除。
- 配置/许可证（按用户选择一并清除）：
  - `C:\Users\FisheryField\AppData\Roaming\RoboDK`
  - `C:\ProgramData\RoboDK`
  - `HKCU\Software\RoboDK`、`HKCU\Software\RoboDK5.9`
  - `HKCU\Software\TheEnigmaProtector2\KeysGenerator\RoboDK`
- 注册表：
  - 卸载项 `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\RoboDK`
  - 文件关联 `.rdk`、`.rdka`、`.rdkbak`、`.rdklic`、`.rdkp` 及 RoboDK 占用的 CAD/NC 扩展名（`.dae`、`.dxf`、`.obj`、`.step`、`.stp`、`.iges`、`.igs`、`.wrl` 等）
  - ProgID：`RoboDK.cadobj`、`RoboDK.dae` 等
  - COM CLSID（krcc64.DLL 相关 5 个）及 .NET Record 项
  - SolidWorks 插件注册 `HKLM\SOFTWARE\SolidWorks\Addins\{DAEBF626-...}`
  - 用户 `.rdk` 文件关联缓存 `FileExts\.rdk`
- 最终搜索：`HKLM\SOFTWARE` / `HKCU\SOFTWARE` 中无 `RoboDK` 键名，`Classes` 中无 `RoboDK` / `krcc64` / `ToolsRoboDKSW` 数据，无 `RoboDK.exe`，无 RoboDK 进程。

## 保留的数据

- `D:\mydata\working things\dobot_arm\RoboDK files 2\`：工作站 `2026-10-15.rdk`、`连续轨迹16.json` 等轨迹文件。
- `D:\mydata\glm-workplace\sim_scripts\`：`TCP真实运动_P2P版.py` 等控制脚本。
- `C:\Users\FisheryField\Documents\RoboDK\`：现有 4,437 文件 / 138,068,470 B（含 `.vscodium2` 编辑器数据），未改动。
- 系统 Python 无 `robodk` 包，无需处理。

## 说明

- `.rdk` 等文件关联已移除；双击 `.rdk` 时 Windows 会询问用哪个程序打开，文件本身不受影响。
- 卸载后未保留配置/许可证副本。
