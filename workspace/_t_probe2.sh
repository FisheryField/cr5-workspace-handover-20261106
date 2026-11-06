#!/bin/sh
echo ===UPTIME===
cat /proc/uptime
echo ===LOCAL_22000===
netstat -lnt 2>/dev/null | grep 22000
wget -q -O- -T 3 http://127.0.0.1:22000/ 2>&1 | head -c 200
echo
echo ===TMP===
ls -la /tmp/ | head -25
echo ===CPUDELTA===
P=$(ps | grep codesyscontrol | grep -v grep | awk '{print $1}')
awk '{print "utime+stime(ticks):", $14+$15}' /proc/$P/stat
sleep 20
awk '{print "utime+stime(ticks):", $14+$15}' /proc/$P/stat
