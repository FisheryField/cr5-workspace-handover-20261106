ls -la /tmp/ecat_mbx 2>/dev/null || echo "NOT FOUND"
chmod +x /tmp/ecat_mbx 2>/dev/null
echo "--- 直接跑（无参数，只打印用法）---"
/tmp/ecat_mbx 2>&1 | head -8
echo "--- 参数不全也应只打印用法，不碰总线 ---"
echo "exit=$?"
