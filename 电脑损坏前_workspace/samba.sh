echo "=== smbd/nmbd processes ==="; ps | grep -E "smbd|nmbd" | grep -v grep
echo "=== listening 139/445 ==="; netstat -tln | grep -E ":139|:445"
echo "=== established to 445/139 ==="; netstat -tn | grep -E ":139|:445"
echo "=== /dobot/bin/etc/smb.conf ==="; cat /dobot/bin/etc/smb.conf
echo "=== /usr/local/samba ==="; ls -la /usr/local/samba 2>/dev/null
echo "=== /usr/local/samba/private ==="; ls -la /usr/local/samba/private 2>/dev/null
echo "=== share path exists? ==="; ls -la /dobot/userdata/project | head -6
echo "=== smbpasswd file? ==="; ls -la /dobot/bin/etc/*passwd* /usr/local/samba/private/* 2>/dev/null | head