chmod +x /tmp/slaveinfo
echo "=== 试运行(不带参数只打印用法) ==="
/tmp/slaveinfo 2>&1 | head -8
echo "rc=$?"