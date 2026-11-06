echo "=== 控制器上的 .app / PLC 应用 ==="
find / -name "*.app" -o -name "*.app_" 2>/dev/null | head -20
echo
echo "=== /home/ftp/PlcLogic ==="
ls -laR /home/ftp/PlcLogic 2>/dev/null | head -40
echo
echo "=== 项目目录 ==="
ls -la /dobot/userdata/CR5_sys_files/project/ 2>/dev/null | head -30
echo
echo "=== codesyscontrol 加载的 .so / 数据文件 ==="
grep -ao "/[a-zA-Z0-9_/\.-]*\.\(so\|app\|dat\)" /proc/378/maps 2>/dev/null | sort -u | head -30
echo
echo "=== PlcLogic / Application 相关路径 ==="
find / -iname "*PlcLogic*" -o -iname "*Application*" 2>/dev/null | grep -av proc | head -20
