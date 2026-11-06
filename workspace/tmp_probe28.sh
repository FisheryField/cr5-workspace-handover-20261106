echo "=== V uptime"; cat /proc/uptime
echo "=== V app"; md5sum /home/ftp/PlcLogic/Application/Application.app /dobot/userdata/codesys/allST/Application.app
echo "=== V update flag"; cat /home/ftp/PlcLogic/Recipe/Update.txt
echo "=== V DONE"