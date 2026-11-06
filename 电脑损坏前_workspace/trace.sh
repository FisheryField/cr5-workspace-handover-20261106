echo "=== now / uptime ==="; date; cat /proc/uptime
echo "=== SavePos now ==="; ls -la /home/ftp/PlcLogic/Recipe/SavePos.txt; od -A d -t x1 /home/ftp/PlcLogic/Recipe/SavePos.txt | head -4
echo "=== files modified 15:24-15:29 ==="
touch -t 202609181524 /tmp/refA; touch -t 202609181529 /tmp/refB
find /dobot /home /opt /etc /usr/local/samba -type f -newer /tmp/refA ! -newer /tmp/refB 2>/dev/null | grep -v lost+found | head -60
echo "=== files modified 14:52-14:57 ==="
touch -t 202609181452 /tmp/refC; touch -t 202609181457 /tmp/refD
find /dobot /home /opt /etc -type f -newer /tmp/refC ! -newer /tmp/refD 2>/dev/null | grep -v lost+found | head -60