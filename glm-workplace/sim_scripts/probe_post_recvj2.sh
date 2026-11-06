#!/bin/sh
# 只读：收口窗口（10:25:00-10:25:29）——覆盖 log~log.12 防轮转
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo '=== [1] 收口后 30 秒窗口 ==='
grep -a '10:25:0[0-9]\|10:25:1[0-9]\|10:25:2[0-9]' "$D"/log "$D"/log.1 "$D"/log.2 "$D"/log.3 "$D"/log.4 "$D"/log.5 "$D"/log.6 "$D"/log.7 "$D"/log.8 "$D"/log.9 "$D"/log.10 "$D"/log.11 "$D"/log.12 2>/dev/null | grep -a -v 'FollowError\|st_collision_load\|torDiffJ1\|PoseTrace\|readSDO\|updateEncoder\|MonitorActual' | head -80
echo '=== [2] 完成/异常关键字 10:25-10:27 ==='
grep -a '10:25:\|10:26:\|10:27:' "$D"/log "$D"/log.1 "$D"/log.2 "$D"/log.3 "$D"/log.4 "$D"/log.5 "$D"/log.6 "$D"/log.7 2>/dev/null | grep -a -i 'finish\|done\|complete\|OnCmd\|disconnect\|timeout\|socket\|closed\|error\|fail\|alarm' | grep -a -v 'FollowError\|st_collision\|torDiff' | head -30
