echo "=== smbd version ==="; /dobot/bin/bin/smbd -V 2>&1 | head -3; /dobot/bin/bin/smbd --version 2>&1 | head -3
echo "=== nmbd version ==="; /dobot/bin/bin/nmbd -V 2>&1 | head -3
echo "=== which libtalloc ==="; ls /dobot/bin/lib/ | grep -i talloc
echo "=== smb.conf full ==="; cat /dobot/bin/etc/smb.conf
echo "=== samba var dir ==="; ls -la /usr/local/samba/var 2>/dev/null