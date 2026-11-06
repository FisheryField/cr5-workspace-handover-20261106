echo "=== date / uptime ==="; date; cat /proc/uptime
echo "=== processes ==="; ps | grep -E "codesys|gcontrol|logServer|redis" | grep -v grep
echo "=== SlaveLog ==="; cat /dobot/userdata/SlaveLog 2>/dev/null | head -20
echo "=== gcontrol log tail ==="; tail -c 900 /dobot/userdata/project/logs/gcontrol/log 2>/dev/null
echo "=== codesys log tail ==="; tail -c 1500 /dobot/userdata/project/logs/codesys/log 2>/dev/null