L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 最近的 EtherCAT / OP / SAFEOP / 状态 相关日志 ==="
tail -6000 $L | grep -aiE "safeop|\bOP\b|ethercat|state|轴|axis|slave" | tail -40
echo
echo "=== 最近 30 行（滤掉心跳）==="
tail -300 $L | grep -avE "RealtimeHeartbeat|algs_framework" | tail -30
