echo "=== /home/ftp/.dobotConfig ==="; ls -la /home/ftp/.dobotConfig
echo "=== StartCnt ==="; cat /home/ftp/.dobotConfig/StartCnt 2>/dev/null
echo "=== redis.conf key lines ==="; grep -nE "^(port|bind|dir|dbfilename|logfile|save)" /dobot/bin/etc/redis.conf | head -20
echo "=== hostapd.conf ==="; cat /etc/hostapd.conf
echo "=== udhcpd.conf (ip range) ==="; grep -nE "start|end|interface|option router|option dns" /etc/udhcpd.conf | head -12
echo "=== /home/ftp/.lib ==="; ls /home/ftp/.lib | head
echo "=== codesys Platforms ==="; ls -la /opt/codesys/Platforms/Linux/Bin | head -20