#!/bin/sh
# 只读：实时负载参数 + 使能/报警状态
echo "=== loadParams（两套路径）==="
cat /dobot/userdata/CR5_sys_files/project/settings/function/loadParams.json 2>/dev/null
echo ""
cat /dobot/userdata/project/settings/function/loadParams.json 2>/dev/null
echo ""
echo "=== 最近报警位 ==="
grep -a 'AlarmSysSetBit' /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -5
echo "=== 使能状态最近记录 ==="
grep -a 'monitorServoUptime' /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -4
