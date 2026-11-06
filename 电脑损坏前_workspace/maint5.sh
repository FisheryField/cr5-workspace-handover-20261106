echo "=== BEFORE ==="; date
for p in $(pidof codesyscontrol); do kill $p; done
for p in $(pidof gcontrol); do kill $p; done
sleep 5
ps | grep -E "codesys|gcontrol" | grep -v grep || echo "stopped"
chmod +x /tmp/ecat_zero
echo "=== J1 (slave 3) 驱动器回零（CiA402 homing method 35）==="
/tmp/ecat_zero home 3
echo "=== HOME_TEST_DONE ==="