#!/bin/sh
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== homeEncoder mentions in all/log (last 10) ==="
grep -n "homeEncoder" $LOG | tail -10
echo ""
echo "=== homeEncoder mentions with timestamps this boot ==="
grep -E "^\[2026-10-10 11:(49|5)" $LOG | grep -i "encoder" | head -10
echo ""
echo "=== SlaveLog: newest file + content head ==="
ls -le /dobot/userdata/SlaveLog | tail -5
NEW=$(ls -t /dobot/userdata/SlaveLog | head -1)
echo "--- $NEW ---"
head -40 "/dobot/userdata/SlaveLog/$NEW"
echo ""
echo "=== slaves online check in all/log ==="
grep -iE "slave.*(online|found|9)" $LOG | grep -E "^\[2026-10-10 11:" | head -8
echo ""
echo "=== any AlarmSysSetBit after reboot? (lines after 395605) ==="
awk 'NR>395605 && /AlarmSysSetBit/ {c++} END {print "count:", c+0}' $LOG
