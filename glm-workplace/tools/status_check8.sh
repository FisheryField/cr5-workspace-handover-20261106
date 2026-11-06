#!/bin/sh
# 只读：用 wget POST 读 ServoParams（BusyBox 无 curl）
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "===== wget POST readServoParams J1 0x6064 ====="
wget -q -O - --timeout=8 \
  --header='Content-Type: application/json' \
  --post-data='{"body":[{"key":"addr606400","servoNum":"J1"}]}' \
  http://127.0.0.1:22000/settings/readServoParams 2>&1
echo
sleep 2
echo "===== 最近的 readSDO 行 ====="
grep -a "readSDO" $LOG | tail -5
