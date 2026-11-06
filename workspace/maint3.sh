echo "=== BEFORE ==="; date
for p in $(pidof codesyscontrol); do kill $p; done
for p in $(pidof gcontrol); do kill $p; done
sleep 5
ps | grep -E "codesys|gcontrol" | grep -v grep || echo "stopped"
chmod +x /tmp/ecat_zero
echo "=== A) 当前 0x6064 / 0x607C（检查上次 J1 写入是否存活）==="
/tmp/ecat_zero read
echo "=== B) 枚举 slave 3 对象字典 ==="
/tmp/ecat_zero sdoinfo 3 > /tmp/sdo3.txt 2>&1
echo "lines=$(wc -l < /tmp/sdo3.txt)"
echo "--- 关键词过滤 ---"
grep -iE "home|offset|zero|calib|param|absolut|encoder|preset" /tmp/sdo3.txt | head -60
echo "--- 字典前 100 行 ---"
head -100 /tmp/sdo3.txt
echo "=== DONE（只读，未写任何参数）==="