#!/bin/sh
echo "=== 是否出现 servoParams.json ==="
ls -la /dobot/userdata/project/settings/function/ 2>/dev/null
echo
echo "=== 最近 3 分钟被创建/修改的文件 ==="
find /dobot /tmp /root -mmin -3 -type f 2>/dev/null | head -20
echo
echo "=== 控制器日志里有没有 sdo 相关行 ==="
grep -a -c 'sdo read\|sdo write\|start read sdo' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null
grep -a 'sdo read\|sdo write\|start read sdo\|readServoParams' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -10
echo
echo "=== 当前时间 ==="
date
