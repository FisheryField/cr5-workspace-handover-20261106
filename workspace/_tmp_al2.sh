#!/bin/sh
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo '=== last 40 non-alarm_io log lines ==='
grep -av 'alarm_io' $L | grep -av RealtimeHeartbeat | tail -n 40
echo
echo '=== gcontrol log dir ==='
ls -la /dobot/userdata/CR5_sys_files/project/logs/gcontrol/ 2>/dev/null | head
tail -n 25 /dobot/userdata/CR5_sys_files/project/logs/gcontrol/* 2>/dev/null | tail -n 30
echo '=== END ==='
