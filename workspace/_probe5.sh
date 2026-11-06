echo '=== mToolServer.log 尾部 40 行 ==='
tail -40 /mToolServer/mToolServer.log 2>/dev/null
echo
echo '=== updateRunResult.log ==='
cat /mToolServer/updateRunResult.log 2>/dev/null
echo
echo '=== controlRunProcess.log 尾部 15 行 ==='
tail -15 /mToolServer/controlRunProcess.log 2>/dev/null
echo
echo '=== /tmp/tUpdate 内容 ==='
ls -laR /tmp/tUpdate/ 2>/dev/null | head -40
echo
echo '=== 最近一次 settVersion（控制器日志）==='
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
grep -a -A14 "settVersion#4492" "$LOG" 2>/dev/null | tail -16
echo
echo '=== 当前时间/uptime/进程 ==='
date; cat /proc/uptime
ps 2>/dev/null | grep -iE "codesys|gcontrol|mTool" | grep -v grep
