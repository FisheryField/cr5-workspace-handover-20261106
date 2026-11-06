#!/bin/sh
# 只读：定位 P5 收口冻结（10:08 与 10:25 两次）在控制器侧的记录
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo '=== [0] 卷目录（确认时间覆盖） ==='
ls -la "$D" | tail -22
echo '=== [1] MovL / JointMovJ 指令痕迹（最近卷） ==='
grep -a -h 'MovL\|JointMovJ\|MovJ' "$D"/log "$D"/log.2 "$D"/log.3 "$D"/log.4 "$D"/log.5 2>/dev/null | tail -25
echo '=== [2] 报警置位 AlarmSysSetBit（log~log.8） ==='
grep -a -h 'AlarmSysSetBit' "$D"/log "$D"/log.2 "$D"/log.3 "$D"/log.4 "$D"/log.5 "$D"/log.6 "$D"/log.7 "$D"/log.8 2>/dev/null | tail -25
echo '=== [3] 碰撞/错误关键字（log~log.8） ==='
grep -a -h -i 'collis\|collision\|Alarm\|error ID' "$D"/log "$D"/log.2 "$D"/log.3 "$D"/log.4 "$D"/log.5 "$D"/log.6 2>/dev/null | grep -a -v 'FollowError' | tail -30
echo '=== [4] 10:08 与 10:25 时段的 MovL 命令行 ==='
grep -a -h 'MovL(' "$D"/log.4 "$D"/log.5 "$D"/log.6 "$D"/log.7 "$D"/log.8 "$D"/log.9 "$D"/log.10 2>/dev/null | tail -20
