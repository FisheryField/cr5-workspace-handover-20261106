#!/bin/sh
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo "=== symlink check ==="
ls -ld /dobot/userdata/project
ls -ld /dobot/userdata/CR5_sys_files/project

echo ""
echo "=== timestamp anchor BEFORE first raw frame (line 398094) ==="
awk 'NR<=398094 && /^\[2026-10-10/ {t=$0} END {print t}' $LOG
echo "=== timestamp anchor BEFORE idle calibrated frame 397757 ==="
awk 'NR<=397757 && /^\[2026-10-10/ {t=$0} END {print t}' $LOG

echo ""
echo "=== ALL timestamped events lines 397757-398320 ==="
awk 'NR>=397757 && NR<=398320 && /^\[2026-10-10/ {print NR": "$0}' $LOG

echo ""
echo "=== ALL PoseTrace lines 398060-398300 (absolute NR) ==="
awk 'NR>=398060 && NR<=398300 && /PoseTrace/ {print NR": "$0}' $LOG

echo ""
echo "=== writeSDO/readSDO since reboot (lines>395605) ==="
awk 'NR>395605 && /SDO/ {print NR": "$0}' $LOG | head -30

echo ""
echo "=== homeEncoder/HomeOffset mentions since reboot ==="
awk 'NR>395605 && tolower($0) ~ /homeencoder|homeoffset|home_offset/ {print NR": "$0}' $LOG | head -10
