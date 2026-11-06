echo "=== log.smbd ==="; cat /usr/local/samba/var/log.smbd
echo "=== log.nmbd ==="; cat /usr/local/samba/var/log.nmbd
echo "=== smbd version ==="; LD_LIBRARY_PATH=/dobot/bin/lib /dobot/bin/bin/smbd -V 2>&1 | head -3
echo "=== does server signing param exist? ==="; LD_LIBRARY_PATH=/dobot/bin/lib /dobot/bin/bin/smbd -b 2>&1 | grep -i "server signing" | head -3