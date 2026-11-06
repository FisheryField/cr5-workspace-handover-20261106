echo '=== 今天 10:00 之后 mToolServer 的全部请求与动作 ==='
grep -a "2026-09-22 10:" /mToolServer/mToolServer.log 2>/dev/null | grep -a -vE "get /protocol/version|get /update/singleStatus" | head -80
echo
echo '=== 今天有没有刷过从站（FoE）==='
grep -a "2026-09-22" /mToolServer/mToolServer.log 2>/dev/null | grep -a -E "updateSlaveFW|start FoE|slaveId|updateFile" | head -30
echo
echo '=== 今天 controller 升级脚本日志 ==='
grep -a "2026-09-22" /mToolServer/controlRunProcess.log 2>/dev/null | head -10
echo
echo '=== 当前运行的控制器版本（重启后）==='
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
grep -a -oE "control *: *[^ ]+" "$LOG" 2>/dev/null | tail -3
echo '=== 最新 settVersion ==='
grep -a -A14 "settVersion#4492" "$LOG" 2>/dev/null | tail -16
echo '=== 本次开机时间 ==='
uptime; date
