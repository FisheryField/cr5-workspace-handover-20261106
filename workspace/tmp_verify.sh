echo "=== R uptime"; cat /proc/uptime; date
echo "=== R app md5"; md5sum /dobot/userdata/codesys/allST/Application.app /home/ftp/PlcLogic/Application/Application.app
echo "=== R procs"; ps | grep -E "codesys|gcontrol" | grep -v grep
echo "=== R DONE"