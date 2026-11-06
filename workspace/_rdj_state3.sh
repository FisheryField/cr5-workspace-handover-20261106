#!/bin/sh
# 给 FollowError 块定时间 + 统计 + 取 gcontrol 错误状态
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "== file size =="
ls -l $LOG
echo "== total FollowError lines in file =="
grep -ac 'FollowError' $LOG
echo "== Move vs Stop FollowError counts =="
grep -ac 'Move FollowError: MoveFollowError Calc' $LOG
grep -ac 'Stop FollowError' $LOG
echo
echo "== timestamped lines in last 6MB (any HH:MM:SS) =="
tail -c 6000000 $LOG | strings | grep -aoE '2026-09-2[0-9] [0-9]{2}:[0-9]{2}:[0-9]{2}[:.][0-9]*' | sort | uniq -c | tail -30
echo
echo "== context: 60 lines around FIRST FollowError occurrence in last 6MB =="
tail -c 6000000 $LOG | strings > /tmp/_alltail.txt
N=$(grep -an 'FollowError' /tmp/_alltail.txt | head -1 | cut -d: -f1)
echo "first FollowError at line $N of tail"
if [ -n "$N" ]; then
  sed -n "$((N-30)),$((N+5))p" /tmp/_alltail.txt | grep -aE '2026-|FollowError|enable|Enable|Motion|motion|servo|Servo|cali|home' | head -40
fi
echo
echo "== last 40 timestamped lines with keywords =="
grep -aE '2026-09-24' /tmp/_alltail.txt | grep -aiE 'enable|disable|error|cali|home|motion|follow|clear|fault' | tail -40
