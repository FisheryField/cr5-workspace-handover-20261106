echo '--- /tmp 下相关文件 ---'
ls -la /tmp/ | grep -E "dryrun|zero_shm" 
echo '--- launch.log ---'
cat /tmp/dryrun2.launch.log 2>/dev/null || echo '(不存在)'
echo '--- dryrun2 目录 ---'
ls -la /tmp/dryrun2/ 2>/dev/null || echo '(不存在)'
echo '--- rounds ---'
wc -l /tmp/dryrun2/rounds.txt 2>/dev/null
echo '--- summary ---'
cat /tmp/dryrun2/summary.txt 2>/dev/null
echo '--- 手动再跑 5 秒看有没有报错 ---'
/tmp/shm_zero_capture.sh manualtest 5 2>&1 | tail -15
echo '--- 结果 ---'
wc -l /tmp/manualtest/rounds.txt 2>/dev/null
head -4 /tmp/manualtest/changes.txt 2>/dev/null
