#!/bin/sh
# 只读：六轴固件版本 0x5000:07（0x3150=3.1.5.0）
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
for i in 1 2 3 4 5 6; do
  wget -q -O - --timeout=8 \
    --header='Content-Type: application/json' \
    --post-data="{\"body\":[{\"key\":\"addr500007\",\"servoNum\":\"J$i\"}]}" \
    http://127.0.0.1:22000/settings/readServoParams > /dev/null 2>&1
  sleep 1
done
sleep 2
grep -a "readSDO#4613\|readSDO#4624" $LOG | grep -a "index=20480" | tail -12
