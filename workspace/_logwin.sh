L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 16:53:44 ~ 16:53:47 窗口 ==="
grep -aE "^\[2026-09-23 16:53:4[4-7]" $L | grep -avE "RealtimeHeartbeat|algs_framework" | tail -60
echo
echo "=== 所有含 addr 或 key 的行（今天）==="
grep -aE "addr|the key" $L | tail -30
