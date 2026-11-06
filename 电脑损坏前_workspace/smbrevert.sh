echo "=== log tail before revert ==="; tail -8 /usr/local/samba/var/log.smbd
echo "=== revert smb.conf ==="
cp -f /dobot/bin/etc/smb.conf.bak-20260918 /dobot/bin/etc/smb.conf && cat /dobot/bin/etc/smb.conf
export LD_LIBRARY_PATH=/dobot/bin/lib:/usr/local/samba/lib:/usr/lib
for p in $(pidof smbd); do kill $p; done
for p in $(pidof nmbd); do kill $p; done
sleep 3
rm -f /usr/local/samba/var/locks/*.pid
/dobot/bin/bin/nmbd -s /dobot/bin/etc/smb.conf -D
sleep 1
/dobot/bin/bin/smbd -s /dobot/bin/etc/smb.conf -D
sleep 3
echo "=== processes ==="; ps | grep -E "smbd|nmbd" | grep -v grep
echo "=== ports ==="; netstat -tln | grep -E ":139|:445"
echo "=== log tail after ==="; tail -6 /usr/local/samba/var/log.smbd