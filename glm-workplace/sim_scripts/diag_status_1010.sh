#!/bin/sh
# diag_status_1010.sh - read-only status check 12 days after v37 checkpoint
# Goals: (a) confirm servo fw / main app / homeEncoder unchanged,
#        (b) locate original Application.app backup (md5 8416cf0e...) for homing fallback,
#        (c) current enable / alarm state from log tail.
# READ-ONLY: no writes on device.

LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
APP=/dobot/userdata/codesys/allST/Application.app
HEJ=/dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json

echo "== 0. device date / uptime =="
date
uptime

echo "== 1. Application.app md5 =="
md5sum "$APP" 2>&1
ls -le /dobot/userdata/codesys/allST/ 2>&1 | head -40

echo "== 2. codesys root listing =="
ls -le /dobot/userdata/codesys/ 2>&1 | head -30

echo "== 3. *.app candidates + md5 =="
for d in /dobot /udisk /tmp /root /mnt /oem; do
  find "$d" -maxdepth 6 -type f -name '*.app' 2>/dev/null
done | sort -u | while read -r f; do
  md5sum "$f" 2>/dev/null
done

echo "== 3b. Application* files any ext =="
for d in /dobot /udisk /tmp /root; do
  find "$d" -maxdepth 6 -type f -name 'Application*' 2>/dev/null
done | sort -u

echo "== 4. archive hints =="
for d in /dobot /udisk; do
  find "$d" -maxdepth 4 -type f \( -name '*.tar*' -o -name '*.zip' -o -name '*.gz' -o -name '*.7z' \) 2>/dev/null
done | head -30

echo "== 5. homeEncoder.json =="
md5sum "$HEJ" 2>&1
cat "$HEJ" 2>&1
echo
ls -le /dobot/userdata/CR5_sys_files/project/settings/function/ 2>&1 | head -30

echo "== 6. log size =="
ls -le "$LOG"
wc -l "$LOG"

echo "== 7. settVersion recent =="
tail -c 400000 "$LOG" | grep -a 'settVersion' | tail -6

echo "== 8. enable/disable recent =="
tail -c 400000 "$LOG" | grep -aE 'robot (enabled|disabled)|CheckEnableDirection' | tail -12

echo "== 9. alarms recent =="
tail -c 400000 "$LOG" | grep -aE 'AlarmSysSetBit|logServoError' | tail -20

echo "== 10. raw tail 8 =="
tail -8 "$LOG"

echo "== 11. SlaveLog tail 5 =="
tail -5 /dobot/userdata/SlaveLog 2>&1

echo "== 12. key procs =="
ps 2>/dev/null | grep -E 'gcontrol|codesys|logServer' | grep -v grep

echo "== done =="
