echo "=== A. stop mToolServer (it holds the EtherCAT bus) ==="
pkill -9 mToolServer
sleep 2
ps | grep -E "mToolServer|codesyscontrol|gcontrol" | grep -v grep
echo ""
echo "=== B. did codesyscontrol come back? ==="
sleep 5
ps | grep -E "codesyscontrol|gcontrol" | grep -v grep
echo ""
echo "=== C. servo fault codes in the main log (last 10) ==="
grep -a "logServoError\|servo error\|Slave.*error\|EMERGENCY slave" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -10
echo ""
echo "=== D. main log line count now (was 635816) ==="
wc -l < /dobot/userdata/CR5_sys_files/project/logs/all/log
echo ""
echo "=== E. listening ports now ==="
netstat -lntp 2>/dev/null | grep -E "22002|codesys|gcontrol|:8080|:29999|:30003" 
echo ""
echo "=== F. mToolServer really gone? ==="
netstat -lnt | grep 22002 || echo "port 22002 closed - OK"
echo "=== DONE ==="
