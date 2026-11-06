#!/bin/sh
# 只读：收口 JointMovJ（柜钟 10:25:00）之后的完成/异常痕迹
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo '=== [1] 10:25:00-10:25:30 全窗口（log.3/log.2） ==='
grep -a '10:25:0\|10:25:1\|10:25:2' "$D"/log.3 "$D"/log.2 2>/dev/null | grep -a -v 'FollowError\|st_collision_load\|torDiffJ1\|PoseTrace\|readSDO\|updateEncoder' | head -70
echo '=== [2] 完成标志 10:25 ==='
grep -a '10:25:' "$D"/log.3 "$D"/log.2 2>/dev/null | grep -a -i 'finish\|done\|complete\|OnCmd\|gCmdFinishFlag' | head -20
echo '=== [3] 驱动/连接异常 10:25-10:28 ==='
grep -a '10:25:\|10:26:\|10:27:\|10:28:' "$D"/log.2 "$D"/log.1 2>/dev/null | grep -a -i 'disconnect\|timeout\|socket\|closed\|error\|fail' | grep -a -v 'FollowError' | head -25
