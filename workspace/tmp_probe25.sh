L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== W 17:25:00-17:25:25 full (noise filtered)"
grep -an "2026-09-24 17:25:0\|2026-09-24 17:25:1\|2026-09-24 17:25:2" $L | grep -av "RealtimeHeartbeat" | grep -av "alarm_io" | grep -av "0000: 86$" | grep -av "conn_timeout" | head -80
echo "=== W DONE"