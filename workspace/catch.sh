echo "=== date ==="; date
echo "=== 最近 20 分钟内被修改的文件（排除 logs）==="
find /dobot /home /etc /opt /usr/bin /tmp /var -type f -mmin -20 2>/dev/null | grep -v "/logs/" | grep -v lost+found | head -40
echo "=== Recipe 目录 ==="
ls -la --time-style=full-iso /home/ftp/PlcLogic/Recipe/ 2>/dev/null || ls -la /home/ftp/PlcLogic/Recipe/
echo "=== SavePos.txt 内容 ==="
od -A d -t x1 /home/ftp/PlcLogic/Recipe/SavePos.txt 2>/dev/null | head -4
echo "=== SaveAxesValue recipe ==="
cat /home/ftp/PlcLogic/Recipe/SaveAxesValue.AxesValues.txtrecipe 2>/dev/null
echo "=== /opt/.zero ==="; cat /opt/.zero 2>/dev/null
echo "=== ac_persistence ==="; ls -la /home/ftp/PlcLogic/ac_persistence/ 2>/dev/null
echo "=== /dobot/userdata/project/redis ==="; ls -la /dobot/userdata/project/redis/ 2>/dev/null
echo "=== 进程 ==="; ps | grep -E "codesys|gcontrol" | grep -v grep