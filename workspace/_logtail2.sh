#!/bin/sh
#现场快照 + 日志尾部拉取(用于本地分析用户那次"没动"的运行)
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== date ==="; date
echo "=== log size ==="; wc -c $LOG
echo "=== df ==="; df -h /dobot /tmp
echo "=== ps ==="; ps | grep -E 'gcontrol|codesyscontrol|mTool' | grep -v grep
echo "=== netstat ==="; netstat -tn 2>/dev/null | grep -E ':29999|:30005|:22000|:22002' | head -30
echo "=== tail pull ==="
tail -c 20971520 $LOG > /tmp/logtail2.bin
md5sum /tmp/logtail2.bin
ls -l /tmp/logtail2.bin
