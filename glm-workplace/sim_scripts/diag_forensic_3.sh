#!/bin/sh
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo "=== 1. SDO writes of 0x607C (home offset) in WHOLE all/log ==="
grep -n "16#607C" $LOG | tail -20

echo ""
echo "=== 2. CheckEnableDirection history (count + samples) ==="
grep -c "CheckEnableDirection" $LOG
grep -n "CheckEnableDirection" $LOG | head -5

echo ""
echo "=== 3. logServoError / deviation lines tail 15 ==="
grep -niE "logServoError|deviation" $LOG | tail -15

echo ""
echo "=== 4. settings/function full file list ==="
ls -le /dobot/userdata/CR5_sys_files/project/settings/function/

echo ""
echo "=== 5. HTTP SDO read: 0x607C home offset J1-J6 (now, alarm state) ==="
wget -q -O - --post-data '{"body":[{"key":"addr607c00","servoNum":"J1"},{"key":"addr607c00","servoNum":"J2"},{"key":"addr607c00","servoNum":"J3"},{"key":"addr607c00","servoNum":"J4"},{"key":"addr607c00","servoNum":"J5"},{"key":"addr607c00","servoNum":"J6"}]}' http://127.0.0.1:22000/settings/readServoParams 2>&1
echo ""
sleep 1
echo "--- readSDO lines (last 12) ---"
grep -n "readSDO" $LOG | tail -12

echo ""
echo "=== 6. HTTP SDO read: 0x6064 actual position J1-J6 (now) ==="
wget -q -O - --post-data '{"body":[{"key":"addr606400","servoNum":"J1"},{"key":"addr606400","servoNum":"J2"},{"key":"addr606400","servoNum":"J3"},{"key":"addr606400","servoNum":"J4"},{"key":"addr606400","servoNum":"J5"},{"key":"addr606400","servoNum":"J6"}]}' http://127.0.0.1:22000/settings/readServoParams 2>&1
echo ""
sleep 1
grep -n "readSDO" $LOG | tail -8

echo ""
echo "=== 7. codesys log: newest files ==="
ls -let /dobot/userdata/CR5_sys_files/project/logs/codesys/ | head -6

echo ""
echo "=== 8. alarm state now: lastAlarmHappened / g_isErr ==="
grep -nE "lastAlarmHappened|monitorErrorStatus" $LOG | tail -4

echo ""
echo "=== 9. latest gActual frame ==="
grep -n "PoseTrace: gActualPosition" $LOG | tail -2
