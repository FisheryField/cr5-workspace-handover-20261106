#!/bin/sh
# 只读：使能前终检 —— 给定 vs 实际 偏差 + 清报警痕迹 + 日志尾部活动
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== 控制器当前时间 ==='
date

echo ''
echo '=== 日志最后 12 行（现在还有什么在动） ==='
tail -12 $LOG | cut -c1-150

echo ''
echo '=== 最近 5 条 monitorErrorStatus ==='
grep -a 'monitorErrorStatus' $LOG | tail -5

echo ''
echo '=== 最近 8 条报警位变化（找 isOn=0 清除痕迹） ==='
grep -an 'AlarmSysSetBit' $LOG | tail -8

echo ''
echo '=== 最新给定值 (PDO0x6062 demand) ==='
grep -a '(PDO0x6062)Position demand' $LOG | tail -2

echo ''
echo '=== 最新实际值 (gActualPosition) ==='
grep -a 'PoseTrace: gActualPosition' $LOG | tail -2

echo ''
echo '=== 最近 3 次 PowerOn/使能 ==='
grep -an 'PowerOn m_powerCnt\|robot enabled\|robot disabled' $LOG | tail -6
