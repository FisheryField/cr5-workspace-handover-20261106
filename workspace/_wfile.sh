echo "=== 写 /tmp/ServoParamsWrite ==="
cat > /tmp/ServoParamsWrite <<'EOF'
{"body":[{"key":"addr200C01","servoNum":"J6","value":0}]}
EOF
chmod 666 /tmp/ServoParamsWrite
ls -la /tmp/ServoParamsWrite; cat /tmp/ServoParamsWrite; echo
echo
echo "=== 等 15 秒, 看 PLC 有没有反应 ==="
sleep 15
ls -la /tmp/ServoParamsWrite
echo
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 日志中 ServoParamsWrite / SDO 相关 ==="
grep -aE "ServoParamsWrite|SDO write|SDO read|SDO timeout|MBX_COE|write ok" $L | tail -15
echo
echo "=== 最近 15 行（滤掉报警/心跳）==="
tail -200 $L | grep -avE "ALARMS:raw|alarm_io|RealtimeHeartbeat|algs_framework" | tail -15
