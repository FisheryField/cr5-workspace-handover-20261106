#!/bin/sh
# diag_postreboot2.sh - verify after user power-cycle: flood stopped, 0x74 cleared, state baseline
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo "== 1. uptime (fresh boot?) =="
date; uptime

echo "== 2. flood stopped? line growth over 10s =="
A=$(wc -l < $LOG); sleep 10; B=$(wc -l < $LOG); echo "lines: $A -> $B (delta $((B-A)))"

echo "== 3. any FollowError flood in fresh boot log? =="
grep -ac 'FollowError' $LOG

echo "== 4. alarms since boot =="
grep -an 'AlarmSysSetBit\|logServoError' $LOG | tail -8

echo "== 5. enable/disable since boot =="
grep -an 'robot enabled\|robot disabled' $LOG | tail -6

echo "== 6. homeEncoder.json intact (3 records expected) =="
ls -le /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json
md5sum /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json

echo "== 7. any 29999/30003 connections since boot =="
grep -an 'local port:29999\|local port:30003' $LOG | tail -6

echo "== done =="
