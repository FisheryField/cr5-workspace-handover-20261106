echo "=== 1) 相关文件是否存在 ==="
ls -la /tmp/ServoParamsWrite /tmp/ServoParams* 2>/dev/null || echo "  /tmp/ServoParamsWrite 不存在"
ls -la /dobot/userdata/project/settings/function/servoParams.json 2>/dev/null || echo "  servoParams.json 不存在"
ls -la /dobot/userdata/project/settings/function/ 2>/dev/null | head -20
echo
echo "=== 2) 触发写路径 POST /settings/modifyServoParams ==="
wget -q -O - --post-data='{"body":[{"key":"addr200118","servoNum":"J6","value":330}]}'   --header='Content-Type: application/json'   http://127.0.0.1:22000/settings/modifyServoParams 2>&1 | head -5
echo
sleep 1
echo "=== 3) 日志尾部 ==="
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
tail -40 $L | grep -avE "RealtimeHeartbeat|algs_framework" | tail -30
