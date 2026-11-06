L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== P all 24 sdo reads"
tail -c 500000 $L | grep -a "readSDO#4624" | awk '{print}' | sed 's/.*readSDO#4624\] //' | tail -30
echo "=== P calibrate uri"
grep -an "calibrate" $L | tail -25
echo "=== DONE"