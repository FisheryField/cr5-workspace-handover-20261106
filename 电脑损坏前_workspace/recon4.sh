echo "=== /dobot/bin/etc ==="; ls -la /dobot/bin/etc
echo "=== /dobot/bin/bin ==="; ls -la /dobot/bin/bin
echo "=== /dobot/bin/lib (count+first 40) ==="; ls /dobot/bin/lib | wc -l; ls -la /dobot/bin/lib | head -40
echo "=== /dobot/bin/lua ==="; ls -laR /dobot/bin/lua | head -60
echo "=== /dobot/bin/log ==="; ls -la /dobot/bin/log | head -20
echo "=== /dobot/userdata ==="; ls -la /dobot/userdata
echo "=== robotType ==="; cat /dobot/userdata/robotType
echo "=== version.conf ==="; cat /dobot/bin/etc/version.conf
echo "=== iscara.conf ==="; cat /dobot/userdata/project/settings/iscara.conf 2>/dev/null | head -60
echo "=== /dobot/userdata/project ==="; ls -la /dobot/userdata/project | head -40
echo "=== project/settings ==="; ls -la /dobot/userdata/project/settings 2>/dev/null | head -30
echo "=== /home/ftp ==="; ls -la /home/ftp | head -40