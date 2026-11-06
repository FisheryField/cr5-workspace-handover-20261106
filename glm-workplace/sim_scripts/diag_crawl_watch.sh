#!/bin/sh
# 只读：连续 3 次采样 gActualPosition（间隔 3s），看臂是否仍在向 P2 蠕动
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
for i in 1 2 3; do
  grep -a 'gActualPosition' "$LOG" | tail -1
  sleep 3
done
echo '--- 给定 ---'
grep -a 'gRobotAxisMove.nextPos' "$LOG" | tail -1
echo '--- 最新 FollowError Calc ---'
grep -a 'FollowError Calc' "$LOG" | tail -2
