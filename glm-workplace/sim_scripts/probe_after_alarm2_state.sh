#!/bin/sh
# 只读：事故2（14:35:48）后的最新实际关节角 + 该时刻前后 PoseTrace + servo2 錯誤上下文
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "===== last 3 gActualPosition (joint) ====="
grep 'gRobotAxisMove.nextPos\|gActualPosition\|(PDO0x6062)' $LOG | tail -n 6
echo
echo "===== last 3 nextPose/DemandPose/ActualPose (cartesian) ====="
grep -E 'PoseTrace: (nextPose|DemandPose|ActualPose)' $LOG | tail -n 6
echo
echo "===== context around line 106074 (servo2 33921) ====="
sed -n '106050,106110p' $LOG | grep -vE 'RealtimeHeartbeat' | head -c 6000
echo done
