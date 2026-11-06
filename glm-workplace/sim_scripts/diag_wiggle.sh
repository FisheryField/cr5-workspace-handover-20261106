#!/bin/sh
# 只读取证：本次 使能→晃动→急停 窗口
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== 控制器时间 ==='
date

en=$(grep -an 'robot enabled ,begin' $LOG | tail -1 | cut -d: -f1)
echo ''
echo "=== 最近一次使能所在日志行: $en ==="
awk -v s=$en 'NR>=s-2 && NR<=s+2' $LOG | cut -c1-160

echo ''
echo '=== 窗口内事件类行（使能/报警/伺服错误/急停） ==='
awk -v s=$en 'NR>=s' $LOG | grep -a 'monitorServoUptime\|AlarmSysSetBit\|logServoError\|monitorErrorStatus\|emergency\|Emergency\|0x74\|gPowerDown\|ClearError\|clearErr' | head -40

echo ''
echo '=== 晃动开始段：三列位置（头 24 条 PoseTrace） ==='
awk -v s=$en 'NR>=s' $LOG | grep -a 'ServoControl()#205[4568]' | head -24 | sed 's/\[INFO\]\[algs\/src\/common\/run.cpp@ServoControl()#//;s/\] PoseTrace: /  /'

echo ''
echo '=== 晃动结束段：三列位置（尾 18 条） ==='
awk -v s=$en 'NR>=s' $LOG | grep -a 'ServoControl()#205[4568]' | tail -18 | sed 's/\[INFO\]\[algs\/src\/common\/run.cpp@ServoControl()#//;s/\] PoseTrace: /  /'

echo ''
echo '=== 窗口内 FollowError 记录（头 12 条） ==='
awk -v s=$en 'NR>=s' $LOG | grep -a 'FollowError' | head -12 | sed 's/\[INFO\]\[algs\/src\/common\/run.cpp@ServoControl()#//'

echo ''
echo '=== 日志最后 5 行（现在状态） ==='
tail -5 $LOG | cut -c1-160
