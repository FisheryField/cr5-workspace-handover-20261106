#!/bin/sh
# 只读：今天报警事件的完整时间线上下文

LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== A. 10:03:44 使能-下坠事件前后 80 行 ==='
grep -an '10:03:4' $LOG | head -3
awk '/10:03:23/,/10:04:20/' $LOG | grep -a 'servo\|Servo\|enable\|disable\|Alarm\|alarm\|0x8\|collision\|safeio\|unio\|PoseTrace\|Error\|error\|PowerOn\|brake\|Brake' | head -80

echo ''
echo '=== B. 09:33 六轴同步报错时刻上下文 ==='
awk '/09:32:3/,/09:33:3/' $LOG | grep -a 'servo\|Servo\|enable\|disable\|Alarm\|alarm\|Error\|error\|safeio\|unio\|PowerOn\|OP-\|opmode\|bus\|EtherCAT\|ecat' | head -60

echo ''
echo '=== C. 今天 0x82/0x83 报警的完整出现史（含复位） ==='
grep -an 'index=0x82\|index=0x83\|index=0x86' $LOG | tail -40

echo ''
echo '=== D. 当前 OP 状态 / 从站状态（最后几条 EtherCAT 线索） ==='
grep -a 'OP state\|AlState\|al_state\|slave.*state\|dc.sync\|Sync0\|bus.*error\|lost\|Lost' $LOG | tail -15

echo ''
echo '=== E. 今天是否有标零/清零动作 ==='
grep -a 'calihome\|HomeNumdone\|clearCalib\|ClearError\|clearRobotErr\|ResetError' $LOG | tail -10
