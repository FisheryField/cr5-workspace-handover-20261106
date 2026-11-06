echo "=== libCmpDobot6Axes.so 基本信息 ==="
ls -la /usr/lib/libCmpDobot6Axes.so /home/ftp/.lib/libCmpDobot6Axes.so 2>/dev/null
md5sum /usr/lib/libCmpDobot6Axes.so /home/ftp/.lib/libCmpDobot6Axes.so 2>/dev/null
echo "=== 该库里的持久化/零点相关符号 ==="
strings /usr/lib/libCmpDobot6Axes.so 2>/dev/null | grep -iE "retain|persist|save|store|home|zero|offset|param" | sort -u | head -30
echo "=== Application.app 信息 ==="
ls -la /home/ftp/PlcLogic/Application/ 2>/dev/null
md5sum /home/ftp/PlcLogic/Application/Application.app 2>/dev/null
echo "=== 与 3.5.4.1 的 Application.app 对比（本地有备份吗）==="
ls -la /home/ftp/PlcLogic/ 2>/dev/null
echo "=== /opt/codesys 版本痕迹 ==="
cat /dobot/bin/etc/version.conf 2>/dev/null; echo