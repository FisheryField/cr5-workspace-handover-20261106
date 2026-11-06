echo '=== 现在时间 / uptime ==='
date; cat /proc/uptime
echo
echo '=== homeEncoder.json（标零会重写它）==='
ls -la /dobot/userdata/project/settings/function/homeEncoder.json
cat /dobot/userdata/project/settings/function/homeEncoder.json
echo
echo '=== SavePos.txt / Recipe ==='
ls -la /home/ftp/PlcLogic/Recipe/ 2>/dev/null
echo
echo '=== 9/23 日志里的标零痕迹 ==='
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
grep -a -n "2026-09-23" "$LOG" 2>/dev/null | grep -a -iE "calibrate|calihome|OnHOMECmd|writeJsonFile|homeEncoder" | tail -30
echo
echo '=== 9/23 的 calibrate/home 请求 ==='
grep -a -oE "2026-09-23 [0-9:.]+.*(POST uri : /calibrate/[a-zA-Z]+|OnHOMECmd|servo calihome (done|not done)[^\"]{0,20})" "$LOG" 2>/dev/null | tail -25
echo
echo '=== mToolServer.log 9/23 的请求 ==='
grep -a "2026-09-23" /mToolServer/mToolServer.log 2>/dev/null | tail -10
