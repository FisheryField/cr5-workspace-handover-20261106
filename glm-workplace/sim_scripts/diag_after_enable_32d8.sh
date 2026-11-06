#!/bin/sh
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
F=/dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json

echo "=== NOW ==="
date
cat /proc/uptime

echo ""
echo "=== 1. enable/disable events (whole boot history tail) ==="
grep -n "monitorServoUptime" $LOG | tail -6

echo ""
echo "=== 2. CheckEnableDirection (new attempts) ==="
grep -n "CheckEnableDirection" $LOG | tail -3

echo ""
echo "=== 3. ALL AlarmSysSetBit since 14:21 boot ==="
awk 'NR>404354 && /AlarmSysSetBit/ {print NR": "$0}' $LOG

echo ""
echo "=== 4. logServoError since 14:21 boot ==="
awk 'NR>404354 && /logServoError/ {print NR": "$0}' $LOG | tail -12

echo ""
echo "=== 5. enable window: timestamped events around last 'robot enabled' ==="
E=$(grep -n "robot enabled" $LOG | tail -1 | cut -d: -f1)
echo "E=$E"
if [ -n "$E" ]; then
  S=$((E-120)); T=$((E+200))
  awk -v s=$S -v t=$T 'NR>=s && NR<=t && /^\[2026-10-10/ {print NR": "$0}' $LOG
fi

echo ""
echo "=== 6. PoseTrace full window around enable (nextPos/6062/gActual) ==="
if [ -n "$E" ]; then
  S=$((E-160)); T=$((E+240))
  awk -v s=$S -v t=$T 'NR>=s && NR<=t && /PoseTrace/ {print NR": "$0}' $LOG
fi

echo ""
echo "=== 7. homeEncoder.json stat + md5 (rewritten?) ==="
ls -le $F
md5sum $F

echo ""
echo "=== 8. SDO read 0x6064 J1-J6 (enabled state) ==="
wget -q -O - --post-data '{"body":[{"key":"addr606400","servoNum":"J1"},{"key":"addr606400","servoNum":"J2"},{"key":"addr606400","servoNum":"J3"},{"key":"addr606400","servoNum":"J4"},{"key":"addr606400","servoNum":"J5"},{"key":"addr606400","servoNum":"J6"}]}' http://127.0.0.1:22000/settings/readServoParams
echo ""
sleep 1
grep -n "readSDO#46" $LOG | tail -14

echo ""
echo "=== 9. SDO read 0x607C J1-J6 ==="
wget -q -O - --post-data '{"body":[{"key":"addr607c00","servoNum":"J1"},{"key":"addr607c00","servoNum":"J2"},{"key":"addr607c00","servoNum":"J3"},{"key":"addr607c00","servoNum":"J4"},{"key":"addr607c00","servoNum":"J5"},{"key":"addr607c00","servoNum":"J6"}]}' http://127.0.0.1:22000/settings/readServoParams
echo ""
sleep 1
grep -n "index=24700" $LOG | tail -6

echo ""
echo "=== 10. LED + alarm state tail ==="
grep -n "MonitorLedProcess#150" $LOG | tail -4
grep -nE "lastAlarmHappened" $LOG | tail -3

echo ""
echo "=== 11. latest gActual ==="
grep -n "PoseTrace: gActualPosition" $LOG | tail -3

echo ""
echo "=== 12. 0x82/0x83/60948/60949 bus errors since boot ==="
awk 'NR>404354 && /0x82|0x83|60948|60949/ {print NR": "$0}' $LOG | head -10
