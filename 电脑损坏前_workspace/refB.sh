echo "=== files changed since ref (whole FS) ==="
find / -path /proc -prune -o -path /sys -prune -o -path /dev -prune -o -path /dobot/userdata/project/logs -prune -o -type f -newer /tmp/refA2 -print 2>/dev/null | grep -v "refA2" | head -60
echo "=== /opt /udisk /var /usr/local /dobot/bin ==="
find /opt /udisk /var /usr/local /dobot/bin -type f -newer /tmp/refA2 2>/dev/null | head -30
echo "=== SavePos/AxesValue now ==="
ls -la /home/ftp/PlcLogic/Recipe/ 2>/dev/null