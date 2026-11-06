#!/bin/sh
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== sdo 上下文（前 30 处）==="
grep -aoE '.{0,90}sdo.{0,140}' $L 2>/dev/null | head -30
echo
echo "=== POST uri 统计 ==="
grep -aoE 'POST uri : [^ ]{0,50}' $L 2>/dev/null | sort | uniq -c | sort -rn | head -20
echo
echo "=== 日志里最后出现的几个时间戳 ==="
grep -aoE '2026-09-23 [0-9]{2}:[0-9]{2}:[0-9]{2}' $L 2>/dev/null | tail -6
