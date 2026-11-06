L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== since the patch reboot: enable/alarm activity ==="
grep -an "2026-09-24 17:5[5-9]\|2026-09-24 1[89]:\|2026-09-24 2[0-3]:" $L | grep -ai "settControlMode\|robot enabled\|robot disabled\|AlarmSysSetBit\|isRequestCalihome\|HomeNumdone\|calihome done\|enableRobot#40" | grep -av "alarm_io\|RealtimeHeartbeat" | tail -25
echo "=== DONE ==="