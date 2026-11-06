#!/bin/sh
echo "=== uptime / procs ==="
cat /proc/uptime
ps -ef 2>/dev/null | grep -E "[c]odesys|[g]control"
echo
echo "=== installed app md5 (expect 9a808cd9dd8f3aa6adaa4de1a34eb9b3) ==="
md5sum /dobot/userdata/codesys/allST/Application.app /home/ftp/PlcLogic/Application/Application.app
echo
echo "=== last 60 lines mentioning alarm/error/deviation/enable ==="
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
grep -a -i "??????\|deviation\|alarm\|error\|fault\|enable\|disable\|calihome\|robotHome\|too large" $L | tail -n 60
echo
echo "=== newest homeEncoder.json entry ==="
tail -c 620 /dobot/userdata/project/settings/function/homeEncoder.json
echo
echo "=== logServoError count today ==="
grep -ac "logServoError" $L
echo "=== END ==="
