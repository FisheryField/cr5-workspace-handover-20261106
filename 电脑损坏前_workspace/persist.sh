echo "=== libCmpDobot6Axes.so 里的文件路径/持久化 ==="
strings /home/ftp/.lib/libCmpDobot6Axes.so 2>/dev/null | grep -E "/(dobot|home|etc|opt|tmp|var|mnt|udisk)|\\.(json|txt|dat|conf|ini|csv|bin)" | sort -u | head -40
echo "=== libCmpDobot6Axes.so 全部路径样字符串 ==="
strings /home/ftp/.lib/libCmpDobot6Axes.so 2>/dev/null | grep -E "^/" | sort -u | head -30
echo "=== libIoDrvDobIO.so 路径 ==="
strings /home/ftp/.lib/libIoDrvDobIO.so 2>/dev/null | grep -E "/(dobot|home|etc|opt|tmp|var|udisk)" | sort -u | head -30
echo "=== 找 CODESYS 运行时与 EtherCAT 主站库 ==="
find /opt /usr /home -name "libIoDrvEtherCAT*" -o -name "libCmp*" -o -name "codesyscontrol" 2>/dev/null | head -25
echo "=== /opt/codesys 目录树 ==="
find /opt/codesys -maxdepth 5 -type d 2>/dev/null | head -25
echo "=== 当前 codesyscontrol 进程与 cwd ==="
ps | grep -i codesys | grep -v grep
ls -la /proc/374/cwd 2>/dev/null; ls -la /proc/374/exe 2>/dev/null