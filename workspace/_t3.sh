ps | grep -E 'codesys|load' | grep -v grep
echo ===NETSTAT===
netstat -lntp 2>/dev/null | grep -E '22000|29999|30005'
echo ===CHECK-RESTART===
# check if codesysload respawns: look at parent of any codesys process, and recent log start
tail -c 2000 /dobot/userdata/project/logs/all/log | grep -a -v Heartbeat | tail -5
