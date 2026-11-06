#!/bin/sh
# 晃动真窗口：10:38:31 PowerOn -> 10:38:35 e-stop 全行 extraction
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== 0. 时间 ==='
date

echo ''
echo '=== 1. 窗口 A：391370-391560（PowerOn 前后到急停释放）非空行全览 ==='
awk 'NR>=391370 && NR<=391560 && NF>0 {print NR": "substr($0,1,145)}' $LOG | head -70

echo ''
echo '=== 2. 窗口 A 内全部 PoseTrace 组（三列+时间） ==='
awk 'NR>=391300 && NR<=391560' $LOG | grep -a 'PoseTrace' | sed 's/\[INFO\]\[algs\/src\/common\/run.cpp@ServoControl()#//;s/\] PoseTrace: /  /' | head -40

echo ''
echo '=== 3. 窗口 B：393150-393260（冷启动后到 10:40:32 急停前）非空行 ==='
awk 'NR>=393150 && NR<=393260 && NF>0 {print NR": "substr($0,1,145)}' $LOG | head -50

echo ''
echo '=== 4. 391560-393150 之间的关键行（10:38:38 释放后到断电前） ==='
awk 'NR>=391560 && NR<=393150' $LOG | grep -a 'enabled\|PowerOn\|Emergency\|Alarm\|0x86\|FollowError\|ServoOn\|servo on\|brake\|Brake' | head -25

echo ''
echo '=== 5. 使能计数第 7 次的 begin 行到底在哪（全日志只有 10:03:44 一条？） ==='
grep -ac 'robot enabled ,begin' $LOG
echo '--- log.1 里有没有:'
grep -ac 'robot enabled ,begin' /dobot/userdata/CR5_sys_files/project/logs/all/log.1

echo ''
echo '=== 6. 10:38:3x 的 0x74/报警位设置 ==='
awk 'NR>=391000 && NR<=391600' $LOG | grep -a 'AlarmSysSetBit\|logServoError\|monitorErrorStatus' | head -15
