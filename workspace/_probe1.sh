LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo '=== date/uptime ==='
date; cat /proc/uptime
echo '=== 日志文件 ==='
if [ -f "$LOG" ]; then echo "found: $LOG"; ls -la "$LOG"; else LOG=/dobot/userdata/project/logs/all/log; echo "fallback: $LOG"; ls -la "$LOG"; fi
echo '=== 最近一次 settVersion 块 ==='
grep -a -A14 "settVersion#4492" "$LOG" 2>/dev/null | tail -16
echo '=== 日志尾部时间戳 ==='
tail -c 800 "$LOG" 2>/dev/null | strings | grep -a -oE "^.2026-[0-9-]+ [0-9:.]+" | tail -3
echo '=== properties ==='
ls -la /dobot/userdata/project/properties/ 2>/dev/null | head -20
echo '=== /tmp/tUpdate ==='
ls -la /tmp/tUpdate/ 2>/dev/null; ls -la /tmp/tUpdate/slave/ 2>/dev/null
echo '=== 版本文件 ==='
cat /etc/version.conf 2>/dev/null; echo; cat /dobot/bin/etc/version.conf 2>/dev/null; echo
echo '=== ash_history 尾部 ==='
tail -20 /root/.ash_history 2>/dev/null
