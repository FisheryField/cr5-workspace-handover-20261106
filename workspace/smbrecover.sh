export LD_LIBRARY_PATH=/dobot/bin/lib:/usr/local/samba/lib:/usr/lib
echo "=== locks dir ==="; ls -la /usr/local/samba/var/locks/
echo "=== remove stale pid files ==="; rm -f /usr/local/samba/var/locks/*.pid; ls -la /usr/local/samba/var/locks/ | grep -i pid
echo "=== testparm ==="; testparm -s /dobot/bin/etc/smb.conf 2>&1 | head -30
echo "=== start nmbd ==="; /dobot/bin/bin/nmbd -s /dobot/bin/etc/smb.conf -D; echo "rc=$?"
sleep 2
echo "=== start smbd ==="; /dobot/bin/bin/smbd -s /dobot/bin/etc/smb.conf -D; echo "rc=$?"
sleep 3
echo "=== processes ==="; ps | grep -E "smbd|nmbd" | grep -v grep
echo "=== ports ==="; netstat -tln | grep -E ":139|:445"
echo "=== log tail ==="; tail -12 /usr/local/samba/var/log.smbd