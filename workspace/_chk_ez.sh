echo "=== 写前 ==="
/tmp/ecat_zero rv 8 0x607C 0 2>/dev/null || echo "  (ecat_zero 不在, 需重传)"
ls -la /tmp/ecat_zero 2>/dev/null || echo "  工具已被重启清掉"
