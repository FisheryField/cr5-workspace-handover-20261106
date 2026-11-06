echo "=== 0) 控制器是否就绪 ==="
wget -q -O - http://127.0.0.1:22000/protocol/version 2>&1 | head -c 200; echo
echo
echo "=== 1) 写门禁文件 (H0C.00 故障复位 = 0) ==="
cat > /dobot/userdata/project/settings/function/servoParams.json <<'EOF'
{"body":[{"key":"addr200C01","servoNum":"J6","value":0}]}
EOF
chmod 666 /dobot/userdata/project/settings/function/servoParams.json
cat /dobot/userdata/project/settings/function/servoParams.json
echo
echo "=== 2) 触发写 (src=files) ==="
wget -q -O - --post-data='{"src":"files"}' http://127.0.0.1:22000/settings/modifyServoParams 2>&1 | head -3
echo
sleep 2
echo "=== 3) 日志 ==="
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
grep -aE "writeSDOthd|parseAndReqSet|writeSDO#|SDOWRCount|readJsonFile" $L | tail -10
echo
echo "=== 4) 判据统计 ==="
printf "  sdo write,      : %s\n" "$(grep -ac 'sdo write,' $L)"
printf "  sdo write fail  : %s\n" "$(grep -ac 'sdo write fail' $L)"
