echo "=== ethercat 工具路径 ==="
for p in /usr/bin /usr/sbin /sbin /bin /usr/local/bin /opt /dobot/bin; do
  if [ -x "$p/ethercat" ]; then echo "FOUND: $p/ethercat"; fi
done
which ethercat 2>/dev/null
echo
echo "=== IgH 主站设备节点 ==="
ls -l /dev/EtherCAT* 2>/dev/null || echo "(无 /dev/EtherCAT*)"
echo
echo "=== 试着列主站（只读）==="
ethercat master 2>&1 | head -20
echo "---"
ethercat slaves 2>&1 | head -20
echo
echo "=== ethercat 支持的命令 ==="
ethercat --help 2>&1 | head -40
