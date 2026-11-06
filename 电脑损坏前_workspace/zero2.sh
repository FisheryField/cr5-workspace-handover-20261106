echo "=== gcontrol log (newest) ==="; cat /dobot/userdata/project/logs/gcontrol/log
echo "=== gcontrol logs keyword grep ==="; grep -i -n -E "zero|calib|encoder|battery|homing" /dobot/userdata/project/logs/gcontrol/log* 2>/dev/null | head -30
echo "=== codesys logs keyword grep ==="; grep -i -n -E "zero|calib|encoder|battery|homing" /dobot/userdata/project/logs/codesys/log /dobot/userdata/project/logs/codesys/log.1 2>/dev/null | head -40
echo "=== all/log keyword grep ==="; grep -i -a -E "zero|calib|encoder|battery" /dobot/userdata/project/logs/all/log 2>/dev/null | head -30
echo "=== codesys log head ==="; head -20 /dobot/userdata/project/logs/codesys/log