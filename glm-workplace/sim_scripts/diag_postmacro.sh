#!/bin/sh
# diag_postmacro.sh - after RoboDK closed: flood status + macro command forensics + zero survival
LOGDIR=/dobot/userdata/CR5_sys_files/project/logs/all
LOG=$LOGDIR/log

echo "== 1. flood stopped? line count twice, 10s apart =="
A=$(wc -l < $LOG); sleep 10; B=$(wc -l < $LOG); echo "lines: $A -> $B"

echo "== 2. macro session commands in log.1 (boot 15:41 -> 15:52 rotation) =="
grep -an 'local port:29999\|local port:30003\|local port:30004\|EnableRobot\|OnMoveJ\|OnMoveL\|OnQueuedCmdStart\|robot enabled\|robot disabled' $LOGDIR/log.1 | tail -40

echo "== 3. alarms this session (both files) =="
grep -an 'AlarmSysSetBit' $LOGDIR/log.1 | tail -6
grep -an 'AlarmSysSetBit' $LOG | tail -6

echo "== 4. SDO read 0x6064 current joint raw (zero survival) =="
curl -s -X POST http://127.0.0.1:22000/settings/readServoParams -H 'Content-Type: application/json' -d '{"body":[{"key":"addr606400","servoNum":"J1"},{"key":"addr606400","servoNum":"J2"},{"key":"addr606400","servoNum":"J3"},{"key":"addr606400","servoNum":"J4"},{"key":"addr606400","servoNum":"J5"},{"key":"addr606400","servoNum":"J6"}]}'
sleep 2
grep -a 'readSDO' $LOG | tail -12

echo "== done =="
