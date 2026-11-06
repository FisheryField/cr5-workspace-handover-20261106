echo "=== 1. identity ==="
uname -a
echo "=== 2. uptime / boot ==="
cat /proc/uptime
echo "=== 3. running processes of interest ==="
ps | grep -E 'codesyscontrol|gcontrol|mToolServer|dobot' | grep -v grep
echo "=== 4. listening TCP ports ==="
netstat -lntp 2>/dev/null || netstat -lnt
echo "=== 5. servo versions (settVersion block, no tail) ==="
grep -a -n "settVersion" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -3
echo "=== 6. homeEncoder.json ==="
cat /dobot/userdata/project/settings/function/homeEncoder.json
echo ""
echo "=== 7. log line count (baseline for later diff) ==="
wc -l < /dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 8. log size ==="
ls -la /dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 9. tUpdate dir ==="
ls -la /tmp/tUpdate/ 2>/dev/null
ls -la /tmp/tUpdate/slave/ 2>/dev/null
echo "=== 10. filesystem write test (tmp) ==="
touch /tmp/_wtest && echo "tmp writable" && rm -f /tmp/_wtest
echo "=== 11. is amrd deployed ==="
ls -la /tmp/amrd /tmp/amscan /tmp/amdump 2>/dev/null
echo "=== DONE ==="
