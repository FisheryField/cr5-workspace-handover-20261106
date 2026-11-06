L=/mToolServer/mToolServer.log
echo "=== every log line from the mToolServer start onward (no filtering) ==="
sed -n '12860,$p' $L
echo ""
echo "=== the decisive result lines ==="
grep -a -n "foe write result" $L | tail -5
echo ""
echo "=== current servo versions from main log (last settVersion block) ==="
grep -a -n "settVersion" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -14
echo "=== DONE ==="
