#!/bin/sh
# 只读：验证 readServoParams 通道是否工作 + 抓最近的 readSDO 行
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "===== curl 原始返回 ====="
curl -s -m 8 -X POST http://127.0.0.1:22000/settings/readServoParams \
  -H 'Content-Type: application/json' \
  -d '{"body":[{"key":"addr606400","servoNum":"J1"}]}'
echo
sleep 2
echo "===== 最近的 readSDO 行（任意 index） ====="
grep -a "readSDO" $LOG | tail -5
echo
echo "===== 日志最后 5 行 ====="
tail -5 $LOG
