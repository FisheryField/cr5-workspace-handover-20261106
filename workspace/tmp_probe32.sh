L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== window 18:03:00 - 18:04:30 ==="
grep -an "2026-09-25 18:0[34]:" $L | grep -av "RealtimeHeartbeat" | grep -av "alarm_io" | grep -av "conn_timeout" | head -60
echo "=== last AlarmSysSetBit lines ==="
grep -an "AlarmSysSetBit" $L | tail -6
echo "=== DONE ==="