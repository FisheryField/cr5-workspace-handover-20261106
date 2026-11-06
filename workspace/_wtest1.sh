cat > /dobot/userdata/project/settings/function/servoParams.json <<'EOF'
{"body":[{"key":"addr200C01","servoNum":"J6","value":0}]}
EOF
chmod 666 /dobot/userdata/project/settings/function/servoParams.json
echo "文件内容:"; cat /dobot/userdata/project/settings/function/servoParams.json; echo
echo "=== 触发写路径 (src=files) ==="
wget -q -O - --post-data='{"src":"files"}' http://127.0.0.1:22000/settings/modifyServoParams 2>&1 | head -3
echo
sleep 1
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 日志 ==="
grep -aE "writeSDOthd|parseAndReqSet|sdo write|SDOWRCount|readJsonFile" $L | tail -12
