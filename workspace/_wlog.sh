L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 写路径相关关键词（全日志统计）==="
for k in "modifyServoParams" "parseAndReqSetServoParams" "create thread to write" "writeSDOthd" "IsWriteFromFile" "start to parse And Req Set" "sdo write" "ServoParamsWrite" "ServoParams"; do
  printf "  %-32s : %s\n" "$k" "$(grep -ac "$k" $L)"
done
echo
echo "=== 18:01 前后所有 modify/Set 相关行 ==="
grep -aE "modifyServoParams|parseAndReqSet|write sdo|IsWriteFromFile|ServoParams" $L | tail -20
echo
echo "=== 全日志里出现过的所有 ServoParams 相关行 ==="
grep -a "ServoParams" $L | tail -10
