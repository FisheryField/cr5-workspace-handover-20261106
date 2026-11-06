echo "=== BEFORE ==="; date
for p in $(pidof codesyscontrol); do kill $p; done
for p in $(pidof gcontrol); do kill $p; done
sleep 5
ps | grep -E "codesys|gcontrol" | grep -v grep || echo "stopped"
chmod +x /tmp/ecat_zero
echo "=== 1) 读取全部伺服：原始位置 + home offset ==="
/tmp/ecat_zero read
echo "=== 2) J1(slave 3) 机制验证：0x607C := 当前原始位置，再看 0x6064 ==="
/tmp/ecat_zero test 3
echo "=== TEST_DONE（暂不 store，可随时改回）==="