#!/bin/sh
# diag_macro_p1stall.sh - post-reboot zero survival + macro P1-stall forensics
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo "== 1. date / uptime =="
date; uptime

echo "== 2. enable/disable + boot boundary since 15:39 =="
grep -an 'robot enabled\|robot disabled' "$LOG" | tail -8

echo "== 3. motion commands since 15:41 (MoveJ/MoveL/ServoJ/QueuedCmd) =="
grep -an 'OnMoveL\|OnMoveJ\|OnServoJ\|OnSpeedJ\|OnQueuedCmdStart\|OnQueuedCmdStopClear' "$LOG" | tail -30

echo "== 4. script status changes since 15:41 =="
grep -an 'script_status\|conn_terminaltrans' "$LOG" | tail -12

echo "== 5. errors/alarms since 15:41 =="
grep -an 'logServoError\|AlarmSysSetBit' "$LOG" | tail -12

echo "== 6. 29999 client connects (macro driver) =="
grep -an 'local port:29999\|local port:30003\|local port:30004' "$LOG" | tail -10

echo "== 7. homing lines after 15:41 (any re-cal?) =="
grep -an 'HomeNumdone\|calihome' "$LOG" | tail -6

echo "== 8. last lines now =="
tail -6 "$LOG" | grep -av 'tcpDispenser\|befor accept\|after accept'

echo "== done =="
