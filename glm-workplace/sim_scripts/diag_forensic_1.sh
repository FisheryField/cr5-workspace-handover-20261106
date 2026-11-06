#!/bin/sh
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
F=/dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json
FUNC=/dobot/userdata/CR5_sys_files/project/settings/function

echo "=== NOW ==="
date
cat /proc/uptime

echo ""
echo "=== A. homeEncoder files (stat + md5 + content) ==="
ls -le $FUNC | grep -i homeEncoder
md5sum $F
echo "--- content ---"
cat $F

echo ""
echo "=== B. log total lines ==="
wc -l $LOG

echo ""
echo "=== C. AlarmSysSetBit tail 25 (with line numbers) ==="
grep -n "AlarmSysSetBit" $LOG | tail -25

echo ""
echo "=== D. monitorServoUptime tail 8 ==="
grep -n "monitorServoUptime" $LOG | tail -8

echo ""
echo "=== E. LED / power markers tail 15 ==="
grep -nE "MonitorLedProcess|outPowerOn|powerstatus" $LOG | tail -15

echo ""
echo "=== F. emergency mentions tail 10 ==="
grep -niE "handleEmergency" $LOG | tail -10

echo ""
echo "=== G. clear-alarm actions tail 10 ==="
grep -niE "ClearAlarm|ClearError|ResetAlarm|clear alarm" $LOG | tail -10

echo ""
echo "=== H. gActualPosition frames after line 397757 ==="
awk 'NR>397757 && /PoseTrace: gActualPosition/ {print NR": "$0}' $LOG

echo ""
echo "=== I. log tail 40 ==="
tail -n 40 $LOG

echo ""
echo "=== J. gcontrol / codesys log dirs ==="
ls -le /dobot/userdata/CR5_sys_files/project/logs/gcontrol/ | tail -6
ls -le /dobot/userdata/CR5_sys_files/project/logs/codesys/ | tail -6
