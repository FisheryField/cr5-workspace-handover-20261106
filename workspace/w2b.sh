chmod +x /tmp/ecat_zero
echo "=== store J1 (slave 3) parameters ==="
/tmp/ecat_zero store 3
echo "=== re-read ==="
/tmp/ecat_zero read
sync
echo "=== reboot ==="
reboot