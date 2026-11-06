#!/bin/sh
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
FUNC=/dobot/userdata/CR5_sys_files/project/settings/function

echo "=== NOW ==="
date
cat /proc/uptime

echo ""
echo "=== SlaveLog (this boot) ==="
cat /dobot/userdata/SlaveLog

echo ""
echo "=== version markers in all/log (tail 20) ==="
grep -nE "SoftVersion|ServoVersion|servo version|3\.1\.5|3\.2\.D|3\.2\.d" $LOG | tail -20

echo ""
echo "=== homeEncoder files + md5 ==="
ls -le $FUNC | grep -i homeEncoder
md5sum $FUNC/homeEncoder.json

echo ""
echo "=== codesys app dir + md5 ==="
ls -le /dobot/userdata/codesys/allST/ 2>/dev/null | head -8
md5sum /dobot/userdata/codesys/allST/*.app 2>/dev/null

echo ""
echo "=== log baseline ==="
wc -l $LOG
grep -n "monitorServoUptime" $LOG | tail -3
grep -n "AlarmSysSetBit" $LOG | tail -6
grep -n "CheckEnableDirection" $LOG | tail -2

echo ""
echo "=== last gActual frames ==="
grep -n "PoseTrace: gActualPosition" $LOG | tail -2

echo ""
echo "=== SDO read 0x607C (home offset) J1-J6 ==="
wget -q -O - --post-data '{"body":[{"key":"addr607c00","servoNum":"J1"},{"key":"addr607c00","servoNum":"J2"},{"key":"addr607c00","servoNum":"J3"},{"key":"addr607c00","servoNum":"J4"},{"key":"addr607c00","servoNum":"J5"},{"key":"addr607c00","servoNum":"J6"}]}' http://127.0.0.1:22000/settings/readServoParams
echo ""
sleep 1
echo "=== SDO read 0x6064 (actual pos) J1-J6 ==="
wget -q -O - --post-data '{"body":[{"key":"addr606400","servoNum":"J1"},{"key":"addr606400","servoNum":"J2"},{"key":"addr606400","servoNum":"J3"},{"key":"addr606400","servoNum":"J4"},{"key":"addr606400","servoNum":"J5"},{"key":"addr606400","servoNum":"J6"}]}' http://127.0.0.1:22000/settings/readServoParams
echo ""
sleep 1
grep -n "readSDO" $LOG | tail -26

echo ""
echo "=== current alarm/error state ==="
grep -nE "lastAlarmHappened|monitorErrorStatus" $LOG | tail -3
echo ""
echo "=== LED last ==="
grep -n "MonitorLedProcess#150" $LOG | tail -3
