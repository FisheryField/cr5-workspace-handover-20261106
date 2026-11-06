#!/bin/sh
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo "=== active servo error IDs since boot 14:21 ==="
awk 'NR>404354 && /logServoError/ {print NR": "$0}' $LOG | tail -10

echo ""
echo "=== monitorErrorStatus / lastAlarmHappened now ==="
grep -nE "monitorErrorStatus|lastAlarmHappened" $LOG | tail -4

echo ""
echo "=== AlarmSysSetBit since boot 14:21 ==="
awk 'NR>404354 && /AlarmSysSetBit/ {print NR": "$0}' $LOG | tail -8

echo ""
echo "=== clearError actions since boot ==="
awk 'NR>404354 && /[Cc]learError/ {print NR": "$0}' $LOG | tail -6

echo ""
echo "=== SDO 0x6064 under new firmware ==="
wget -q -O - --post-data '{"body":[{"key":"addr606400","servoNum":"J1"},{"key":"addr606400","servoNum":"J2"},{"key":"addr606400","servoNum":"J3"},{"key":"addr606400","servoNum":"J4"},{"key":"addr606400","servoNum":"J5"},{"key":"addr606400","servoNum":"J6"}]}' http://127.0.0.1:22000/settings/readServoParams
echo ""
sleep 1
grep -n "readSDO#46" $LOG | tail -16

echo ""
echo "=== idle gActual frames since boot 14:21 ==="
awk 'NR>404354 && /PoseTrace: gActualPosition/ {print NR": "$0}' $LOG | tail -3
