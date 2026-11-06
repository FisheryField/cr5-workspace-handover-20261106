echo "=== 重启前快照 ==="
date
ls -la /tmp/ecat_mbx
echo "=== 执行重启 ==="
sync
(sleep 2; reboot) &
echo "reboot 已下发"
