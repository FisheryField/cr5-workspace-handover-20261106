chmod +x /tmp/shm_zero_capture.sh
sh -n /tmp/shm_zero_capture.sh && echo SYNTAX_OK
echo "--- 15 秒自检（看覆盖率与每轮耗时）---"
time /tmp/shm_zero_capture.sh selftest2 15 2>&1 | tail -25
echo "--- regions ---"
cat /tmp/selftest2/regions.txt
echo "--- summary ---"
cat /tmp/selftest2/summary.txt
echo "--- 轮数 / 时间跨度 ---"
wc -l < /tmp/selftest2/rounds.txt; head -2 /tmp/selftest2/rounds.txt; tail -2 /tmp/selftest2/rounds.txt
echo "--- changes（16 秒静止期间应该很少）---"
head -12 /tmp/selftest2/changes.txt 2>/dev/null || echo "(无变化)"
echo "--- base 文件大小 ---"
ls -la /tmp/selftest2/base/ | head
