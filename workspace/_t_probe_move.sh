echo ===NOW===
date
echo ===MAINLOG tail80===
tail -80 /dobot/userdata/CR5_sys_files/project/logs/all/log
echo ===TODAY enabled/disabled===
grep -a -E 'robot (enabled|disabled)' /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -12
echo ===TODAY calihome===
grep -a -i 'calihome' /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -12
echo ===TODAY motion keywords===
grep -a -i -E 'jog|movej|movel|jointmove|domotion|startmov|axismove|ptp' /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -20
echo ===CONN===
netstat -tn 2>/dev/null | grep -E ':(29999|30003|30004|30005|22000|22) ' | head -20
echo ===HOMEENC tail===
tail -c 600 /dobot/userdata/project/settings/function/homeEncoder.json
