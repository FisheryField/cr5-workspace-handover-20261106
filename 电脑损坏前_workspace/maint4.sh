echo "=== BEFORE ==="; date
for p in $(pidof codesyscontrol); do kill $p; done
for p in $(pidof gcontrol); do kill $p; done
sleep 5
ps | grep -E "codesys|gcontrol" | grep -v grep || echo "stopped"
chmod +x /tmp/ecat_zero
echo "=== A) 6 轴关键对象对比 (6063/6064/607C/60B0) ==="
/tmp/ecat_zero compare
echo "=== B) slave 3 厂商私有对象 0x5000-0x5007 全量 ==="
/tmp/ecat_zero vendor 3 > /tmp/vendor3.txt 2>&1
cat /tmp/vendor3.txt
echo "=== DONE（纯只读）==="