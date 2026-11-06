echo "=== date/uptime ==="; date; cat /proc/uptime
echo "=== version.conf ==="; cat /etc/version.conf 2>/dev/null; echo; cat /dobot/bin/etc/version.conf 2>/dev/null; echo
echo "=== codesys 启动日志里的 retain 相关 ==="
grep -a -o -E ".{0,60}(retain|Retain|persistent|Persistent).{0,80}" /dobot/userdata/project/logs/codesys/log 2>/dev/null | tail -8
echo "=== codesys 启动时的 SDO 写入（看有没有 607C / 60B0）==="
grep -a -o -E "SDO write (ok|fail): Address: [0-9]+ Index: 16#[0-9A-F]+ SubIndex: [0-9]+" /dobot/userdata/project/logs/codesys/log 2>/dev/null | sed "s/Address: [0-9]* //" | sort -u | head -40
echo "=== 有没有新的零点相关文件 ==="
find /dobot/userdata /home/ftp /etc -type f \( -iname "*zero*" -o -iname "*home*" -o -iname "*calib*" -o -iname "*retain*" \) 2>/dev/null | grep -v logs | head -20
echo "=== Recipe 目录 ==="; ls -la /home/ftp/PlcLogic/Recipe/ 2>/dev/null
echo "=== ac_persistence ==="; ls -la /home/ftp/PlcLogic/ac_persistence/ 2>/dev/null