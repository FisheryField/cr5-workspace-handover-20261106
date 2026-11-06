chmod +x /tmp/shm_zero_capture.sh
echo "--- 语法检查 ---"
sh -n /tmp/shm_zero_capture.sh && echo "SYNTAX_OK"
echo "--- 5 秒自检运行 ---"
/tmp/shm_zero_capture.sh selftest 5 2>&1 | tail -20
echo "--- 产物 ---"
ls -la /tmp/selftest/ 2>/dev/null
echo "--- regions.txt ---"
cat /tmp/selftest/regions.txt 2>/dev/null
echo "--- summary.txt ---"
cat /tmp/selftest/summary.txt 2>/dev/null
echo "--- rounds 数 / changes ---"
wc -l /tmp/selftest/rounds.txt 2>/dev/null
head -5 /tmp/selftest/changes.txt 2>/dev/null || echo "(无变化)"
