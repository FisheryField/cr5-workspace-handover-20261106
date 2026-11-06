echo "=== baseline: log line count before starting ==="
wc -l < /mToolServer/mToolServer.log
echo ""
echo "=== ports BEFORE ==="
netstat -lnt | awk '{print $4}' | sort > /tmp/_ports_before.txt
wc -l < /tmp/_ports_before.txt
echo ""
echo "=== starting mToolServer ==="
cd /mToolServer
nohup ./mToolServer > /tmp/mToolServer_stdout.txt 2>&1 &
echo "started, pid=$!"
sleep 4
echo ""
echo "=== is it running? ==="
ps | grep mToolServer | grep -v grep
echo ""
echo "=== ports AFTER (new ones) ==="
netstat -lnt | awk '{print $4}' | sort > /tmp/_ports_after.txt
comm -13 /tmp/_ports_before.txt /tmp/_ports_after.txt
echo "--- full listen list (for reference) ---"
netstat -lntp 2>/dev/null | grep mToolServer
echo ""
echo "=== stdout of mToolServer ==="
cat /tmp/mToolServer_stdout.txt
echo ""
echo "=== new log lines since start ==="
tail -20 /mToolServer/mToolServer.log
echo "=== DONE ==="
