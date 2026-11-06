L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 写路径关键词计数（对比之前全是 0）==="
for k in "create thread to write" "parseAndReqSetServoParams" "writeSDOthd" "IsWriteFromFile" "start to parse And Req Set" "sdo write" "ServoParamsWrite"; do
  printf "  %-32s : %s\n" "$k" "$(grep -ac "$k" $L)"
done
echo
echo "=== 相关日志行 ==="
grep -aE "create thread to write|parseAndReqSet|writeSDOthd|IsWriteFromFile|start to parse And Req Set|sdo write|ServoParams" $L | tail -30
echo
echo "=== 最近 25 行（滤掉报警和心跳）==="
tail -300 $L | grep -avE "RealtimeHeartbeat|algs_framework|ALARMS:raw|alarm_io" | tail -25
