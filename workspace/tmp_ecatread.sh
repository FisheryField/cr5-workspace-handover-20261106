chmod +x /tmp/ecat_zero
ls -la /tmp/ecat_zero
echo "=== K killing codesyscontrol"
pkill -9 codesyscontrol
sleep 3
ps | grep -E "codesys|gcontrol" | grep -v grep
echo "=== K read (DS121 slaves: 0x6064 / 0x607C / 0x60B0)"
/tmp/ecat_zero read
echo "=== K DONE"