#!/bin/sh
# 只读：找伺服固件版本行 + 14:13 开机后的关键标记
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "===== 当前 log 里 3.1.5 / DS. 版本行 ====="
grep -an "3\.1\.5\|DS\." $LOG | head -15
echo
echo "===== 14:13 开机后的 calihome / HomeNumdone ====="
grep -an "calihome\|HomeNumdone" $LOG | tail -8
echo
echo "===== 14:13 开机后的 PoseTrace 最近 3 条 ====="
grep -a "PoseTrace: gActualPosition" $LOG | tail -3
echo
echo "===== 使能状态最近 2 条 ====="
grep -a "robot enabled\|robot disabled" $LOG | tail -2
