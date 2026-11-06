#!/bin/sh
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== non-alarm_io lines, last 50 ==="
grep -av "alarm_io" $L | grep -av "RealtimeHeartbeat" | tail -n 50
echo
echo "=== lines with join/pos/cali/offset (ascii) ==="
grep -aiv "alarm_io" $L | grep -aiE "cali|offset|deviat|jointpos|posdiff|homestate|enabl|disabl|limit" | tail -n 40
echo "=== END ==="
