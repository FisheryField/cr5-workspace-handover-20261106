echo "=== NUM-DATE"; date; cat /proc/uptime
echo "=== NUM-PROCS"; ps | grep -E "codesys|gcontrol|mTool|dobot" | grep -v grep
echo "=== NUM-LOGTAIL"
tail -c 400000 /dobot/userdata/CR5_sys_files/project/logs/all/log | grep -av alarm_io | grep -av RealtimeHeartbeat | tail -70
echo "=== NUM-ERRGREP"
tail -c 400000 /dobot/userdata/CR5_sys_files/project/logs/all/log | grep -ai "error\|fail\|alarm\|deviat\|joint" | grep -av alarm_io | grep -av RealtimeHeartbeat | tail -40
echo "=== NUM-DONE"