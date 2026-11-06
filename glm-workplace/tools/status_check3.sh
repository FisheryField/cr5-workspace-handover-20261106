#!/bin/sh
# 只读：0x7c 发生时刻 + 本次开机启动序列 + 版本信息
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "===== 0x7c 前后带时间戳的行（线号 605480~605520） ====="
sed -n '605480,605520p' $LOG | grep -a "^\[2026\|index=0x7c\|FollowError" | head -30
echo
echo "===== 本次开机（14:13 左右）的启动/版本标记 ====="
grep -an "PowerOn\|m_powerCnt" $LOG | tail -5
echo
grep -an "servo.*version\|Version\|version" $LOG | grep -av "PoseTrace" | tail -15
echo
echo "===== 0x7c 在整个当前 log 里出现的行号 ====="
grep -an "index=0x7c" $LOG | head -20
echo
echo "===== 最近 5 分钟有没有新报警（对照时间 14:43+） ====="
tail -2000 $LOG | grep -a "AlarmSysSetBit" | tail -5
tail -3 $LOG
