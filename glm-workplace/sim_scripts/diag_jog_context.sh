#!/bin/sh
# diag_jog_context.sh - joint coords around the 14:45 J5 jog + 0x92 events
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo "== A. joint coord lines 14:44-14:46 =="
sed -n '411560,411960p' "$LOG" | grep -a 'getCoorDAndSendToAlgs' | head -4
sed -n '411560,411960p' "$LOG" | grep -a 'getCoorDAndSendToAlgs' | tail -4

echo "== B. any 0x92 isOn=0 (clear) lines =="
grep -ac 'index=0x92,isOn=0' "$LOG"

echo "== C. disable/enable events 14:40-15:11 =="
grep -an 'robot enabled\|robot disabled' "$LOG" | awk -F: '$1 > 405600' | head -10

echo "== D. panel jog events today =="
grep -an 'panelJog' "$LOG" | head -12

echo "== done =="
