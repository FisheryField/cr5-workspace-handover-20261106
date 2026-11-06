L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== W window 665195-665345"
sed -n '665195,665345p' $L | grep -av "RealtimeHeartbeat" | grep -av "0000: 86"
echo "=== W END"