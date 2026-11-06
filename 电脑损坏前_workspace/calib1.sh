echo "=== /opt/.zero ==="; cat /opt/.zero; echo "--- save.sh ---"; cat /opt/save.sh
echo "=== tools available ==="; for t in strings sqlite3 redis-cli objdump; do printf "%s: " "$t"; command -v $t || echo MISSING; done
echo "=== grep calib/zero in configs+lua+sh ==="
grep -rniE "calib|zero|标定|零点|encoder|origin|home" /dobot/bin/etc /dobot/userdata/project/settings /dobot/bin/lua /dobot/bin/dobot.sh /etc/init.d 2>/dev/null | head -70
echo "=== dobot.db tables ==="; /dobot/bin/bin/sqlite3 /dobot/bin/dobot.db ".tables" 2>&1 | head -20
echo "=== dobot.db schema ==="; /dobot/bin/bin/sqlite3 /dobot/bin/dobot.db ".schema" 2>&1 | head -40
echo "=== calibration/Demarcate project dirs ==="; ls -la /dobot/userdata/project/project/calibration 2>/dev/null; echo "---"; ls -la /dobot/userdata/project/project/Demarcate 2>/dev/null
echo "=== settings/coordinate ==="; ls -la /dobot/userdata/project/settings/coordinate 2>/dev/null | head -20