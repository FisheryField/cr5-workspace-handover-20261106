#!/bin/sh
# 只读：今天报警首发诱因 + 报警史 + 标定记录现状
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== A. 今天第一条报警（全天首发时刻与内容） ==='
grep -an 'AlarmSysSetBit' $LOG | grep -a '10-10' | head -8 || grep -an 'AlarmSysSetBit' $LOG | tail -60 | head -8

echo ''
echo '=== B. 09:30:00-09:32:45 窗口：掉使能前发生了什么 ==='
awk '/09:3[012]:/' $LOG | grep -a 'Alarm\|error\|Error\|collision\|Collision\|disable\|enable\|0x8\|Follow\|over\|Over\|temp\|Temp\|bus\|unio\|safeio' | head -40

echo ''
echo '=== C. 标定记录 homeEncoder.json ==='
cat /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json 2>/dev/null || cat /dobot/userdata/project/settings/function/homeEncoder.json 2>/dev/null

echo ''
echo '=== D. 当前错误状态（最后一条 monitorErrorStatus） ==='
grep -a 'monitorErrorStatus' $LOG | tail -3

echo ''
echo '=== E. 0x83 报警全天出现次数 ==='
grep -ac 'index=0x83' $LOG
