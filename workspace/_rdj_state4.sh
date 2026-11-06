#!/bin/sh
# 给 FollowError 定时间（字节偏移对比法）+ 找 19:2x 后的日志活动
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "== offsets of timestamped lines today 19:00-19:59 =="
grep -abo '2026-09-24 19:[0-2][0-9]' $LOG | tail -20
echo "== offsets of timestamped lines today 18:00-18:59 =="
grep -abo '2026-09-24 18:[0-5][0-9]' $LOG | tail -8
echo "== last 5 FollowError offsets =="
grep -abo 'FollowError Calc' $LOG | tail -5
echo "== first FollowError offset after 20MB =="
grep -abo 'FollowError Calc' $LOG | awk -F: '$1>20000000' | head -3
echo "== last 'gActualPosition' offsets =="
grep -abo 'gActualPosition' $LOG | tail -5
echo
echo "== what is written between offset 26.0MB and EOF (recent activity) =="
tail -c 700000 $LOG | strings | grep -avE 'FollowError' | tail -50
