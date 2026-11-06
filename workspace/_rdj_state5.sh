#!/bin/sh
echo "== homeEncoder.json =="
cat /dobot/userdata/project/settings/function/homeEncoder.json
echo
echo "== log size now (was 26773487 at 19:38) =="
ls -l /dobot/userdata/CR5_sys_files/project/logs/all/log
echo "== fresh tail: last 300 bytes as text =="
tail -c 300 /dobot/userdata/CR5_sys_files/project/logs/all/log | strings | tail -5
echo "== FE spam still growing? count again (was 178094 at 19:38) =="
grep -ac 'FollowError' /dobot/userdata/CR5_sys_files/project/logs/all/log
echo "== robot enabled state via dashboard port =="
printf 'RobotEnable()\r\n' | timeout 2 nc 127.0.0.1 29999 | head -2
