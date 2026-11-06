echo "=== date/uptime ==="; date; cat /proc/uptime
echo "=== 6轴组件 libCmpDobot6Axes.so ==="
ls -la /usr/lib/libCmpDobot6Axes.so /home/ftp/.lib/libCmpDobot6Axes.so 2>/dev/null
md5sum /usr/lib/libCmpDobot6Axes.so /home/ftp/.lib/libCmpDobot6Axes.so 2>/dev/null
echo "=== retain 相关 (关键) ==="
grep -a -o -E ".{0,40}(retain area|No retain|RETAIN).{0,60}" /dobot/userdata/project/logs/codesys/log 2>/dev/null | tail -6
echo "=== 开机 SDO 写入索引集合 ==="
grep -a -o -E "SDO write ok: Address: [0-9]+ Index: 16#[0-9A-F]+" /dobot/userdata/project/logs/codesys/log 2>/dev/null | sed "s/Address: [0-9]* //" | sort -u
echo "=== ac_persistence ==="; ls -la /home/ftp/PlcLogic/ac_persistence/ 2>/dev/null
echo "=== Recipe ==="; ls -la /home/ftp/PlcLogic/Recipe/ 2>/dev/null
echo "=== Application.app ==="; md5sum /home/ftp/PlcLogic/Application/Application.app 2>/dev/null; ls -la /home/ftp/PlcLogic/Application/ 2>/dev/null
echo "=== 零点相关文件 ==="
find /dobot/userdata /home/ftp /etc /opt -type f \( -iname "*zero*" -o -iname "*home*" -o -iname "*retain*" -o -iname "*persist*" \) 2>/dev/null | grep -v logs | head -20
echo "=== version.conf ==="; cat /etc/version.conf; echo; cat /dobot/bin/etc/version.conf; echo
echo "=== /dobot/bin 里新增的文件 ==="; ls -la /dobot/bin/ | head -30