echo "=== smbclient -L localhost ==="
/dobot/bin/bin/smbclient -L //127.0.0.1 -N 2>&1 | head -25
echo "=== smbstatus ==="
/dobot/bin/bin/smbstatus 2>&1 | head -15
echo "=== connect to own share ==="
/dobot/bin/bin/smbclient //127.0.0.1/project -N -c "ls" 2>&1 | head -20