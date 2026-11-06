echo '=== /tmp 占用 ==='
df -h /tmp
echo
echo '=== /tmp 里的大块 ==='
du -sk /tmp/* 2>/dev/null | sort -rn | head -20
echo
echo '=== 清理我自己的测试产物 ==='
rm -rf /tmp/selftest /tmp/selftest2 /tmp/manualtest /tmp/selftest.tar.gz /tmp/selftest2.tar.gz /tmp/manualtest.tar.gz /tmp/dryrun /tmp/dryrun2 /tmp/dryrun.tar.gz /tmp/dryrun2.tar.gz /tmp/dryrun*.launch.log /tmp/TAG.tar.gz
echo '清理后:'
df -h /tmp
