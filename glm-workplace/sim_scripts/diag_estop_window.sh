#!/bin/sh
# diag_estop_window.sh - full context of the 15:31:20 homing attempt that ended in e-stop
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo "== A. anchor: last HomeNumdone : 2 =="
grep -an 'HomeNumdone' "$LOG" | tail -6

echo "== B. full window from first HomeNumdone after 15:31 to e-stop (+400 lines, noisy filtered) =="
A=$(grep -an 'HomeNumdone : 0' "$LOG" | tail -1 | cut -d: -f1)
echo "anchor line = $A"
sed -n "${A},$((A+400))p" "$LOG" | grep -av 'tcpDispenser\|befor accept\|after accept\|getCoorDAndSendToAlgs\|PoseTrace\|panelJog\|conn_req_dir' | head -80

echo "== C. servo errors in window =="
grep -an 'logServoError' "$LOG" | tail -8

echo "== D. enable/disable transitions =="
grep -an 'robot enabled\|robot disabled' "$LOG" | tail -6

echo "== E. homeEncoder.json state =="
ls -le /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json
md5sum /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json

echo "== done =="
