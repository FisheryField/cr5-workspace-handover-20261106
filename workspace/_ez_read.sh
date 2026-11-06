chmod +x /tmp/ecat_zero
echo "=== ecat_zero read (SOEM 接管总线, 只读) ==="
/tmp/ecat_zero read 2>&1 | head -60
