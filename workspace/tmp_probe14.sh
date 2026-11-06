L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== E around enable"
grep -an "2026-09-24 17:08:1[0-9]\|2026-09-24 17:08:2[0-9]\|2026-09-24 17:08:3[0-9]" $L | grep -av "RealtimeHeartbeat" | grep -av "^.*0000: 86$" | grep -av "conn_timeout" | head -70
echo "=== E DONE"