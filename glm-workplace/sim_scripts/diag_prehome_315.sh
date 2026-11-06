#!/bin/sh
# diag_prehome_315.sh - read-only pre-homing check after flash-back to 3.1.5.0
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
APP=/dobot/userdata/codesys/allST/Application.app
HEJ=/dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json

echo "== 1. date / uptime =="
date; uptime

echo "== 2. servo + module versions (last block) =="
grep -a 'settVersion' "$LOG" | tail -14

echo "== 3. main app md5 (allST) =="
md5sum "$APP"
ls -le /dobot/userdata/codesys/allST/

echo "== 4. original app available for fallback =="
md5sum /dobot/userdata/codesys/BACKUP_ORIGINAL/Application.app
ls -le /dobot/userdata/codesys/BACKUP_ORIGINAL/

echo "== 5. homing attempts since flash (HomeNumdone/calihome) =="
grep -an 'HomeNumdone\|calihome\|servo home\|ServoHome' "$LOG" | tail -10

echo "== 6. enable/disable recent =="
grep -an 'robot enabled\|robot disabled' "$LOG" | tail -6

echo "== 7. alarms recent =="
grep -an 'AlarmSysSetBit\|logServoError' "$LOG" | tail -8

echo "== 8. homeEncoder.json state =="
md5sum "$HEJ"
ls -le "$HEJ"

echo "== 9. log size =="
wc -l "$LOG"

echo "== done =="
