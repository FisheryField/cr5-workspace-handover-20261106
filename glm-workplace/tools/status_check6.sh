#!/bin/sh
# 只读：确认伺服固件版本（HTTP SDO 读 0x5000:07）+ 14:13 重启后 0x82/MBX 情况
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "===== 读六轴固件版本 0x5000:07（HTTP readServoParams，只读） ====="
i=1
while [ $i -le 6 ]; do
  curl -s -m 8 -X POST http://127.0.0.1:22000/settings/readServoParams \
    -H 'Content-Type: application/json' \
    -d "{\"body\":[{\"key\":\"addr500007\",\"servoNum\":\"J$i\"}]}" > /dev/null 2>&1
  sleep 1
  i=$((i+1))
done
sleep 2
echo "--- 日志里的 readSDO 版本行 ---"
grep -a "readSDO" $LOG | grep -a "5000" | tail -8
echo
echo "===== 14:13 重启后 0x82 / MBX 错误 ====="
awk '/2026-09-28 14:1[3-9]|2026-09-28 14:[2-9]/' $LOG 2>/dev/null | grep -a "index=0x82\|MBX" | tail -10
echo "（空 = 重启后没有）"
