#!/bin/sh
echo ===TCPDUMP===
which tcpdump; ls -l /usr/sbin/tcpdump /bin/tcpdump 2>/dev/null
echo ===JOINTS===
python3 -c "print('n/a')" 2>/dev/null
echo ===HOMEENC===
cat /dobot/userdata/project/settings/function/homeEncoder.json | head -c 800
echo
echo ===LASTSTATE===
grep -a 'jointHomeState\|HomeNumdone\|calihome' /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -6
