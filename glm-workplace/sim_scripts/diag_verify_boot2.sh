#!/bin/sh
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== line numbers: last 15 AlarmSysSetBit ==="
grep -n "AlarmSysSetBit" $LOG | tail -15
echo ""
echo "=== last 0x7e line number ==="
L=$(grep -n "index=0x7e" $LOG | tail -1 | cut -d: -f1)
echo "L=$L"
echo ""
echo "=== context around last 0x7e (nearest timestamps) ==="
sed -n "$((L-8)),$((L+12))p" $LOG
echo ""
echo "=== line numbers: last 6 PoseTrace gActual ==="
grep -n "PoseTrace: gActualPosition" $LOG | tail -6
echo ""
echo "=== context around last gActual frame ==="
P=$(grep -n "PoseTrace: gActualPosition" $LOG | tail -1 | cut -d: -f1)
echo "P=$P"
sed -n "$((P-6)),$((P+6))p" $LOG
echo ""
echo "=== enable/disable mentions with timestamps since 11:49 ==="
grep -E "^\[2026-10-10 11:(49|5[0-9])" $LOG | grep -iE "enable|alarm|error|fault" | head -20
