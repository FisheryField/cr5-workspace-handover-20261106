#!/bin/sh
F=/dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== date / proc uptime ==="
date
cat /proc/uptime
echo ""
echo "=== homeEncoder.json stat + md5 ==="
ls -le $F
md5sum $F
echo ""
echo "=== homeEncoder.json content ==="
cat $F
echo ""
echo "=== homeEncoder-related files in function dir ==="
ls -le /dobot/userdata/CR5_sys_files/project/settings/function/ | grep -i homeEncoder
echo ""
echo "=== boot markers: monitorServoUptime (last 3) ==="
grep "monitorServoUptime" $LOG | tail -3
echo ""
echo "=== PowerOn markers (last 3) ==="
grep "PowerOn" $LOG | tail -3
echo ""
echo "=== alarms since boot: AlarmSysSetBit (last 10) ==="
grep "AlarmSysSetBit" $LOG | tail -10
echo ""
echo "=== PoseTrace gActual (last 4) ==="
grep "PoseTrace: gActualPosition" $LOG | tail -4
echo ""
echo "=== log last 20 lines ==="
tail -n 20 $LOG
