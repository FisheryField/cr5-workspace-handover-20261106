LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo '=== 控制器版本线索 ==='
grep -a -oE "3\.5\.[0-9]\.[0-9]-stable[a-z0-9-]*" "$LOG" 2>/dev/null | sort -u | tail -5
grep -a -oE "control *: *[^ ]+" "$LOG" 2>/dev/null | tail -3
echo '=== 开机横幅 ==='
grep -a -m3 -E "CR5_CC162|version" "$LOG" 2>/dev/null | head -5
echo '=== ecat_zero 是否还在 ==='
ls -la /tmp/ecat_zero /tmp/ecat_read /tmp/slaveinfo 2>/dev/null || echo "不在（/tmp 已被重启清空）"
echo '=== 当前 EtherCAT/伺服进程 ==='
ps 2>/dev/null | grep -iE "codesys|gcontrol|mToolServer" | grep -v grep
echo '=== mc 状态 ==='
echo "RobotMode" > /dev/null
echo '=== 磁盘 ==='
df -h | head -8
