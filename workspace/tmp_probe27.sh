L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== W 17:32:00-17:32:10"
grep -an "2026-09-24 17:32:0" $L | grep -av "RealtimeHeartbeat" | grep -av "alarm_io" | grep -av "conn_timeout" | head -50
echo "=== W alarm bit activity after reboot"
grep -an "AlarmSysSetBit" $L | tail -8
echo "=== W DONE"