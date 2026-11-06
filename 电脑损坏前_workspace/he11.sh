echo "=== SlaveInfos recipe ==="
cat /home/ftp/PlcLogic/Recipe/SlaveInfos.SlaveInfos.txtrecipe
echo
echo "=== /mToolServer 与伺服固件 ==="
ls -la /mToolServer/
find / -xdev -name "*Servo*" -o -xdev -name "*FOE*" -o -xdev -name "*FOE*" 2>/dev/null | head -20
echo "=== 日志里的伺服版本/固件信息 ==="
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
grep -a -o -iE ".{0,60}(servo ?version|firmware|Version of slave|FW ?ver|revision).{0,60}" $L | sort -u | head -25
echo "=== 日志里的 3.1.5 ==="
grep -a -o -iE ".{0,60}3\.1\.5.{0,60}" $L | sort -u | head -10
echo "=== libCmpDobot6Axes strings ==="
strings /usr/lib/libCmpDobot6Axes.so | grep -i -E "cali|home|encoder|0x6|sdo|offset" | head -40
echo "=== 版本文件 ==="
cat /dobot/bin/etc/version* 2>/dev/null; ls /dobot/bin/etc/ | head -30