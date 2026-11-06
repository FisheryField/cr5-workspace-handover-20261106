echo '=== 时间 / 运行时长 ==='
date; cat /proc/uptime
echo
echo '=== 版本 JSON（看 servo6）==='
wget -qO- --post-data='' http://127.0.0.1:22000/settings/version 2>/dev/null || curl -s -X POST http://127.0.0.1:22000/settings/version
echo
echo '=== settVersion（控制器日志最近一次）==='
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
grep -a -A14 "settVersion#4492" "$LOG" 2>/dev/null | tail -16
echo
echo '=== mToolServer.log 里跟 slave 8 / servo 相关的最近记录 ==='
tail -60 /mToolServer/mToolServer.log 2>/dev/null | grep -a -E "slave|FoE|update|file1" | tail -20
echo
echo '=== mToolServer.log 尾部 12 行（看最后一次操作）==='
tail -12 /mToolServer/mToolServer.log 2>/dev/null
