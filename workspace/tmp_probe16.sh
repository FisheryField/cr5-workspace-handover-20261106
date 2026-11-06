L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== T window 676088-676130"
sed -n '676088,676130p' $L | grep -av "RealtimeHeartbeat" | grep -av "alarm_io"
echo "=== T DONE"