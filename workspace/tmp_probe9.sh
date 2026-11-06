L=/dobot/userdata/CR5_sys_files/project/logs/all/log
tail -c 400000 $L | grep -a "readSDO" | tail -30
echo "=== DONE"