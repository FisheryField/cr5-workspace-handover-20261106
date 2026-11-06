echo "=== now/uptime ==="; date; cat /proc/uptime
echo "=== SavePos.txt ==="; ls -la /home/ftp/PlcLogic/Recipe/SavePos.txt; od -A d -t x1 /home/ftp/PlcLogic/Recipe/SavePos.txt | head -4
echo "=== SaveAxesValue recipe ==="; cat /home/ftp/PlcLogic/Recipe/SaveAxesValue.AxesValues.txtrecipe 2>/dev/null
echo "=== recently modified files (last 10 min) ==="
touch -t 202609181540 /tmp/r1; find /dobot/userdata /home/ftp /etc -type f -newer /tmp/r1 2>/dev/null | grep -v lost+found | grep -v "/logs/" | head -20