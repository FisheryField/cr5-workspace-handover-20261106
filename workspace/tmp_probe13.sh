L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== Y around 16:43:34 controlMode"
sed -n '664600,664665p' $L | grep -av "RealtimeHeartbeat" | grep -av "0000: 86"
echo "=== Y DONE"