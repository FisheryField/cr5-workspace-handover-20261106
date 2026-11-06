echo "=== uptime ==="; cat /proc/uptime; uptime 2>/dev/null
echo "=== now ==="; date
echo "=== boot-ish: smbd start time ==="; ls -la /usr/local/samba
echo "=== who is on 445 ==="; netstat -tn | grep -E ":139|:445"
echo "=== dmesg-ish last boot ==="; head -1 /proc/stat