L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 全部 HTTP uri (去重) ==="
grep -a -o -E "uri : /[^ ]*" $L | sort -u | head -120
echo
echo "=== HOMEParams / cali 相关日志 ==="
grep -a -o -iE ".{0,50}HOMEParams.{0,60}" $L | tail -10
grep -a -o -iE ".{0,40}(calihome|caliHome|CaliHome).{0,60}" $L | sort -u | head -20
echo "=== settings 目录树 ==="
find /dobot/userdata/project/settings -type f | head -60
echo "=== libdataSvr 里的 uri 字符串 ==="
strings /dobot/bin/lib/libdataSvr.so.1.0.0 | grep -a -E "^/[a-zA-Z]" | sort -u | head -80