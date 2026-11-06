echo "=== who references /opt/save.sh or .zero ==="
grep -rln "save.sh\|/opt/.zero" /dobot/bin /opt /home /etc /dobot/userdata/project/settings /dobot/userdata/project/project 2>/dev/null | head -10
echo "=== gcontrol strings: zero/calib/ABZ/encoder ==="
strings /dobot/bin/gcontrol | grep -iE "zero|calib|abz|encoder" | sort -u | head -50
echo "=== getVersion strings ==="
strings /dobot/bin/getVersion | grep -iE "zero|calib|abz|encoder" | sort -u | head -20
echo "=== algs/dataSvr/process libs ==="
for f in /dobot/bin/lib/libalgs_framework.so.1.0.0 /dobot/bin/lib/libdataSvr.so.1.0.0 /dobot/bin/lib/libprocessPlugin.so.1.0.0; do echo "-- $f"; strings $f 2>/dev/null | grep -iE "zero|calib" | sort -u | head -25; done
echo "=== Application.app strings ==="
strings /home/ftp/PlcLogic/Application/Application.app | grep -iE "save.sh|zero|calib" | sort -u | head -40
echo "=== dobot_setting table ==="
/dobot/bin/bin/sqlite3 /dobot/bin/dobot.db "select key,value from dobot_setting;" 2>&1 | head -60
echo "=== redis keys ==="
/dobot/bin/bin/redis-cli -h 127.0.0.1 -p 6379 keys "*" 2>/dev/null | head -70