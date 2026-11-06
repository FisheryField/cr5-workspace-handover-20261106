echo "=== 内核模块 ==="
lsmod 2>/dev/null | head -30
echo
echo "=== /sys/module 里的 ethercat 相关 ==="
ls /sys/module 2>/dev/null | grep -iE "ether|ec_|igh" 
echo
echo "=== 用户态 ethercat 工具 ==="
for p in /usr/bin /usr/sbin /sbin /bin /usr/local/bin /opt; do ls $p 2>/dev/null | grep -iE "ethercat|slaveinfo|eoe" ; done
echo "(以上为空则没有)"
echo
echo "=== /opt 与常见 CODESYS 路径 ==="
ls /opt 2>/dev/null
ls -d /var/opt/codesys* /etc/ethercat* /opt/etherlab 2>/dev/null
echo
echo "=== 内核里有没有 EtherCAT 主站线索 ==="
cat /proc/modules 2>/dev/null | grep -iE "ether|ec_" 
grep -ail ethercat /proc/*/maps 2>/dev/null | head
echo
echo "=== codesyscontrol 打开的网口/socket ==="
ls -l /proc/374/fd 2>/dev/null | grep -aE "socket|packet" | head -5
echo
echo "=== 控制器上有没有我们已经放过去的工具 ==="
ls -la /tmp/ecat* /tmp/slaveinfo* /dobot/ecat* 2>/dev/null
echo
echo "=== 网络接口 ==="
ifconfig -a 2>/dev/null | grep -aE "^eth|HWaddr"
