#!/bin/sh
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== SlaveLog (file, this boot mtime 11:49:50) ==="
cat /dobot/userdata/SlaveLog
echo ""
echo "=== nearest timestamp BEFORE line 397757 (calibrated frame) ==="
awk 'NR<=397757 && /^\[2026-10-10/ {t=$0} END {print t}' $LOG
echo ""
echo "=== nearest timestamp BEFORE line 393810 ==="
awk 'NR<=393810 && /^\[2026-10-10/ {t=$0} END {print t}' $LOG
echo ""
echo "=== any RAW-frame gActual after reboot (lines>395605)? ==="
awk 'NR>395605 && /PoseTrace: gActualPosition/ {print NR": "$0}' $LOG
