LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo '=== 本次开机(08:3x)附近的版本行 ==='
grep -a -n "2026-09-22 08:3" "$LOG" 2>/dev/null | head -3
echo '--- 开机后 200 行内的 control/version 行 ---'
awk '/2026-09-22 08:3[0-9]/ {found=NR} found && NR>=found && NR<=found+400' "$LOG" 2>/dev/null | grep -a -oE "(control *: *[^ ]+|mainControl[^,]*|V?3\.5\.[0-9]\.[0-9][^ ,]*)" | sort -u | head -20
echo '=== 设置文件里的版本 ==='
cat /dobot/userdata/project/properties/controllerType.json 2>/dev/null; echo
ls -la /home/ftp/PlcLogic/Application/ 2>/dev/null
md5sum /home/ftp/PlcLogic/Application/Application.app 2>/dev/null
echo '=== /dobot/bin 版本标记 ==='
cat /dobot/bin/etc/version.conf 2>/dev/null; echo
ls -la /dobot/bin/ 2>/dev/null | head -12
