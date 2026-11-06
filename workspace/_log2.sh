L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 最近 80 行（过滤心跳）==="
tail -400 $L | grep -avE "RealtimeHeartbeat|algs_framework" | tail -70
