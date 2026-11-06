#!/bin/sh
# diag_posthome_315.sh - post-homing forensics: why is the new zero "not clean"
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
HEJ=/dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json

echo "== A. all HomeNumdone lines today =="
grep -an 'HomeNumdone' "$LOG" | tail -20

echo "== B. all calihome lines today =="
grep -an 'calihome' "$LOG" | tail -20

echo "== C. homeEncoder.json now =="
md5sum "$HEJ"
ls -le "$HEJ"
cat "$HEJ"

echo "== D. alarms in 15:22-15:35 window =="
grep -an 'AlarmSysSetBit\|logServoError' "$LOG" | awk -F'[][]' '{print}' | tail -25

echo "== E. enable/disable after 15:22 =="
grep -an 'robot enabled\|robot disabled' "$LOG" | tail -6

echo "== F. recent joint readouts (set to algs) =="
grep -an 'set to algs' "$LOG" | tail -6

echo "== G. homeEncoder write events =="
grep -an 'writeJsonFile.*homeEncoder\|readJsonFile.*homeEncoder' "$LOG" | tail -8

echo "== H. /calibrate http requests today =="
grep -an '/calibrate' "$LOG" | tail -10

echo "== done =="
