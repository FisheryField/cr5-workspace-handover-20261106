echo "=== V uptime"; cat /proc/uptime
echo "=== V flags"; cat /home/ftp/PlcLogic/Recipe/Update.txt; od -An -tx1 /home/ftp/PlcLogic/Recipe/SavePos.txt | head -2
echo "=== V app"; md5sum /home/ftp/PlcLogic/Application/Application.app
echo "=== V alarm spam (0000: 86 present?)"
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
tail -c 60000 $L | grep -ac "0000: 86"
echo "=== V last control-mode lines"
grep -an "settControlMode : \|robot enabled\|robot disabled" $L | tail -6
echo "=== V DONE"