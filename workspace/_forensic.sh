#!/bin/sh
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 16:20 之后的 sdo/参数 相关行 ==="
grep -aoE '.{0,60}(readServoParams|exitSDOWRThd|SDOWR|sdo read|sdo write|wkc|ServoParams).{0,120}' $L 2>/dev/null | tail -25
echo
echo "=== servoParams.json 是否出现 ==="
ls -la /dobot/userdata/project/settings/function/servoParams.json 2>/dev/null || echo "(不存在)"
find /dobot -name '*servoParam*' -o -name '*ServoParam*' 2>/dev/null | head -10
echo
echo "=== 最近 10 分钟新文件 ==="
find /dobot /tmp -mmin -10 -type f 2>/dev/null | head -15
echo
echo "=== 日志尾部 ==="
tail -c 400 $L 2>/dev/null
echo
echo "=== 现在时间 ==="; date
