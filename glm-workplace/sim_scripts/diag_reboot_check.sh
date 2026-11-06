#!/bin/sh
# diag_reboot_check.sh - confirm possible ~15:10 reboot + investigate 0x92 alarms
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo "== A. uptime now =="
date; uptime

echo "== B. boot markers today (logServer start / system init) =="
grep -an 'logServer.*start\|SystemInit\|board_init\|gcontrol.*start' "$LOG" | tail -6

echo "== C. 0x92 alarm timestamps (context) =="
sed -n '411600,411615p' "$LOG" | head -16
echo "---"
sed -n '411948,411958p' "$LOG" | head -12

echo "== D. what is near line 441349 (the 15:10:26 boundary) =="
sed -n '441330,441360p' "$LOG" | head -32

echo "== E. log line count now =="
wc -l "$LOG"

echo "== done =="
