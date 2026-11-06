echo '=== mToolServer 目录 ==='
ls -la /mToolServer/ 2>/dev/null | head -20
echo '=== 是否在运行 ==='
ps 2>/dev/null | grep -i mtool | grep -v grep || echo '未运行（按需拉起）'
echo '=== 端口线索 ==='
netstat -lntp 2>/dev/null | head -25
echo '=== /dobot/bin/etc 里的端口配置 ==='
grep -rl "mTool" /dobot/bin/etc /etc 2>/dev/null | head -5
echo '=== 9/16 的升级日志（找 slaveId 参数）==='
grep -a -oE "(slaveId|updateType|file1|file2)[^,;&\"]*" /mToolServer/mToolServer.log 2>/dev/null | sort -u | head -20
echo '=== mToolServer.log 最后修改时间与大小 ==='
ls -la /mToolServer/mToolServer.log 2>/dev/null
echo '=== /tmp 现状 ==='
ls -la /tmp/ 2>/dev/null | head -15
