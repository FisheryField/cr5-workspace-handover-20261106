echo "=== backup ==="
cp -f /dobot/bin/etc/smb.conf /dobot/bin/etc/smb.conf.bak-20260918 && ls -la /dobot/bin/etc/smb.conf*

cat > /dobot/bin/etc/smb.conf <<'EOF'
[global]
        workgroup = root
        security = user
        client lanman auth = yes
        lanman auth = yes
        map to guest = bad user
        guest account = root
        protocol = SMB2
        max protocol = SMB2
        server signing = mandatory
        client signing = mandatory

[project]
        comment = project
        path = /dobot/userdata/project
        available = yes
        browseable = yes
        public = yes
        guest ok = yes
        writable = yes
EOF

echo "=== new smb.conf ==="; cat /dobot/bin/etc/smb.conf
echo "=== restarting samba ==="
export LD_LIBRARY_PATH=/dobot/bin/lib:/usr/local/samba/lib:/usr/lib
for p in $(pidof smbd); do kill -9 $p; done
for p in $(pidof nmbd); do kill -9 $p; done
sleep 2
/dobot/bin/bin/nmbd -s /dobot/bin/etc/smb.conf -D
sleep 1
/dobot/bin/bin/smbd -s /dobot/bin/etc/smb.conf -D
sleep 3
echo "=== processes ==="; ps | grep -E "smbd|nmbd" | grep -v grep
echo "=== ports ==="; netstat -tln | grep -E ":139|:445"
echo "=== log tail ==="; tail -15 /usr/local/samba/var/log.smbd