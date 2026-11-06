#!/bin/sh
# diag_prehome_1010.sh - focused read-only checks before the homing decision
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo "== A. homing attempts today (HomeNumdone / calihome / homeEncoder writes) =="
grep -an 'HomeNumdone\|calihome\|homeEncoder' "$LOG" | tail -20

echo "== B. context around the 15:05:01 disable =="
grep -an '15:04:5[0-9]\|15:05:0[0-5]' "$LOG" | grep -av 'tcpDispenser\|befor accept\|after accept' | head -40

echo "== C. any 0x86/0x82/0x83/alarm since 14:21 boot =="
grep -an 'AlarmSysSetBit\|logServoError' "$LOG" | awk -F: '$1 > 405000' | tail -10

echo "== D. one stable joint readback during the 1937s enable (PoseTrace sample) =="
grep -an '14:3[3-9]:\|14:4[0-9]:' "$LOG" | grep -a 'PoseTrace' | head -3

echo "== E. enable counter lines today =="
grep -an 'robot enabled\|robot disabled' "$LOG" | tail -8

echo "== done =="
