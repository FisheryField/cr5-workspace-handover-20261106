echo '=== 保留的归档 ==='
ls -la /tmp/*.tar.gz 2>/dev/null
echo
echo '=== 删除 shm_focus32 解包目录（PC 上已有同名 tar.gz，且 /tmp 内的 .tar.gz 保留）==='
rm -rf /tmp/shm_focus32
echo '删除后:'
df -h /tmp
echo
echo '=== 5 秒验证运行 ==='
/tmp/shm_zero_capture.sh verify 5 2>&1 | tail -6
echo 'rounds:'; wc -l /tmp/verify/rounds.txt 2>/dev/null
echo 'changes 前 4 行:'; head -4 /tmp/verify/changes.txt 2>/dev/null || echo '(无变化)'
echo 'tar 大小:'; ls -la /tmp/verify.tar.gz 2>/dev/null
echo '清理验证产物'; rm -rf /tmp/verify /tmp/verify.tar.gz
df -h /tmp
