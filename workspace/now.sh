echo "=== date/uptime ==="; date; cat /proc/uptime
echo "=== SavePos ==="; ls -la /home/ftp/PlcLogic/Recipe/SavePos.txt; od -A d -t x1 /home/ftp/PlcLogic/Recipe/SavePos.txt | head -4
echo "=== samba/startcnt ==="; ls -la /usr/local/samba 2>/dev/null | head -3