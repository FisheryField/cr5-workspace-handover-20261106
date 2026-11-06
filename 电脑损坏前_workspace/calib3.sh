echo "=== who references save.sh ==="
find /dobot/bin /opt /home /etc /dobot/userdata/project/settings /dobot/userdata/project/project -type f -size -3M 2>/dev/null | xargs grep -l "save\.sh" 2>/dev/null | head -10
echo "=== who references /opt/.zero ==="
find /dobot/bin /opt /home /etc -type f -size -3M 2>/dev/null | xargs grep -l "/opt/\.zero" 2>/dev/null | head -10
echo "=== gcontrol strings ==="
timeout 20 strings /dobot/bin/gcontrol | grep -iE "zero|calib|abz" | sort -u | head -60
echo "=== algs framework strings ==="
timeout 20 strings /dobot/bin/lib/libalgs_framework.so.1.0.0 | grep -iE "zero|calib" | sort -u | head -30
echo "=== Application.app strings ==="
timeout 30 strings /home/ftp/PlcLogic/Application/Application.app | grep -iE "save\.sh|zero|calib" | sort -u | head -40
echo "=== dobot_setting ==="
timeout 15 /bin/sqlite3 /dobot/bin/dobot.db "select key,value from dobot_setting;" 2>&1 | head -60
echo "=== redis keys ==="
timeout 10 /dobot/bin/bin/redis-cli -h 127.0.0.1 -p 6379 keys "*" 2>/dev/null | head -80
echo "=== calibration project files ==="
cat /dobot/userdata/project/project/calibration/src0.lua; echo "--- prj.json ---"; cat /dobot/userdata/project/project/calibration/prj.json; echo; echo "--- Demarcate src0.lua ---"; cat /dobot/userdata/project/project/Demarcate/src0.lua
echo "=== calibration-like project dirs across models ==="
ls -d /dobot/userdata/*_sys_files/project/project/*alib* /dobot/userdata/*_sys_files/project/project/*Demarcate* 2>/dev/null | head -20
echo "=== tool.json / user.json ==="
cat /dobot/userdata/project/settings/coordinate/tool.json; echo "---"; cat /dobot/userdata/project/settings/coordinate/user.json