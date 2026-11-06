L=/dobot/userdata/CR5_sys_files/project/logs/all/log
sed -n '638605,638670p' $L | grep -av "RealtimeHeartbeat" | grep -av "0000: 86"
echo "=== DONE"