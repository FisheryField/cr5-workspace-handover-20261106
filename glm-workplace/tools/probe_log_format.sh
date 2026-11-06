#!/bin/sh
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== head 3 ==="
head -3 "$LOG"
echo "=== tail 3 ==="
tail -3 "$LOG"
echo "=== date now ==="
date
echo "=== count PoseTrace ==="
grep -a -c 'PoseTrace' "$LOG"
echo "=== sample PoseTrace 2 ==="
grep -a 'PoseTrace' "$LOG" | tail -2
echo "=== count 10:09 ==="
grep -a -c '10:09:' "$LOG"
echo "=== any 10-13 ==="
grep -a -m 2 '10-13' "$LOG"
echo "=== grep home done last ==="
grep -a 'servo calihome done' "$LOG" | tail -2
