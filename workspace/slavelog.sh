echo "=== full SlaveLog ==="; cat /dobot/userdata/SlaveLog
echo "=== getVersion strings (ethercat?) ==="; strings /dobot/bin/getVersion 2>/dev/null | grep -iE "ec_|slave|ethercat|encoder|zero|version" | head -30
echo "=== slaveinfo strings (functions) ==="; strings /dobot/userdata/slaveinfo 2>/dev/null | grep -iE "ec_|slave|ethercat|encoder|zero|version|info" | head -30