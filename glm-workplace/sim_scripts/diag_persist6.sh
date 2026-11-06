#!/bin/sh
# gcontrol 层对比 + 冷启动后窗口细读 + 零点文件定位
G=/dobot/userdata/CR5_sys_files/project/logs/gcontrol
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== 0. 时间 ==='
date

echo ''
echo '=== 1. 健康 boot 的 gcontrol 日志（log.2，08:57）全文 ==='
cat $G/log.2 2>/dev/null | head -80

echo ''
echo '=== 2. 病态期 gcontrol 日志（log.1，10:36）全文 ==='
cat $G/log.1 2>/dev/null | head -60

echo ''
echo '=== 3. 当前 gcontrol 日志（冷启动后）全文 ==='
cat $G/log 2>/dev/null | head -60

echo ''
echo '=== 4. 冷启动 codesys init 完成后到文件尾的关键事件（393722 起） ==='
awk 'NR>=393722 && /2026-10-10 10:4/ && /PowerOn|enable|Enable|Servo|servo|Alarm|Emergency|FollowError|0x86|Safety|SafeIO/ {print NR": "substr($0,1,150)}' $LOG | head -40

echo ''
echo '=== 5. 冷启动后所有 PoseTrace 三列（头 12 组） ==='
awk 'NR>=393722' $LOG | grep -a 'ServoControl()#205[4568]' | head -12 | sed 's/\[INFO\]\[algs\/src\/common\/run.cpp@ServoControl()#//;s/\] PoseTrace: /  /'

echo ''
echo '=== 6. 零点/定基相关文件搜盘 ==='
find /dobot/userdata -iname '*zero*' -o -iname '*calib*' -o -iname '*homing*' 2>/dev/null | grep -v codesys/BACKUP | head -20

echo ''
echo '=== 7. 关键参数文件里搜偏置类键名 ==='
grep -rli 'offset\|zero' /dobot/userdata/CR5_sys_files/project/settings/ 2>/dev/null | head -10
