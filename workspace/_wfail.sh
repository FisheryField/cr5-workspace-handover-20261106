L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 精确统计 ==="
printf "  sdo write fail      : %s\n" "$(grep -ac 'sdo write fail' $L)"
printf "  sdo write,          : %s\n" "$(grep -ac 'sdo write,' $L)"
printf "  start write sdo tp  : %s\n" "$(grep -ac 'start write sdo tp' $L)"
printf "  end sdo write       : %s\n" "$(grep -ac 'end sdo write' $L)"
echo
echo "=== sdo write fail 的全部内容 ==="
grep -a "sdo write fail" $L | tail -20
echo
echo "=== 18:05:31 前后所有相关行 ==="
grep -aE "^\[2026-09-23 18:05:3[01]" $L | grep -avE "ALARMS:raw|alarm_io|RealtimeHeartbeat" | head -40
