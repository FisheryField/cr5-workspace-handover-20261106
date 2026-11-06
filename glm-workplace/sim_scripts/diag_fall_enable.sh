#!/bin/sh
# diag_fall_enable.sh - forensics: fall-on-reenable after power cycle at P1 pose
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo "== 1. uptime / now =="
date; uptime

echo "== 2. enable/disable timeline (tail) =="
grep -an 'robot enabled\|robot disabled' $LOG | tail -8

echo "== 3. alarms / servo errors (tail) =="
grep -an 'AlarmSysSetBit' $LOG | tail -10
grep -an 'logServoError' $LOG | tail -10

echo "== 4. flood check: line growth over 8s =="
A=$(wc -l < $LOG); sleep 8; B=$(wc -l < $LOG); echo "lines: $A -> $B (delta $((B-A)))"
echo "FollowError lines in current log: $(grep -ac 'FollowError' $LOG)"

echo "== 5. window around LAST enable =="
E=$(grep -an 'robot enabled' $LOG | tail -1 | cut -d: -f1)
echo "last enable at line $E"
sed -n "$((E-30)),$((E+120))p" $LOG | grep -a 'PoseTrace\|FollowError\|AlarmSysSetBit\|logServoError\|enableRobot\|settControlMode\|updateEncoderData\|homeEncoder\|readSDO\|setZero' | head -50

echo "== 6. last PoseTrace before now (pose continuity) =="
grep -a 'PoseTrace' $LOG | tail -4

echo "== done =="
