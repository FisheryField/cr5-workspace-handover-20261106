echo "=== 1) 六轴当前关节值 ==="
wget -q -O - http://127.0.0.1:22000/protocol/exchange 2>/dev/null | tr ',' '\n' | grep -aA1 -E "joint[0-9]|controlMode|powerState" | head -40
echo
echo "=== 2) homeEncoder.json (上次标定的记录) ==="
cat /dobot/userdata/project/settings/function/homeEncoder.json 2>/dev/null
echo
echo "=== 3) 该文件历史/修改时间 ==="
ls -la /dobot/userdata/project/settings/function/homeEncoder.json 2>/dev/null
echo
echo "=== 4) 标定相关日志(最近) ==="
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
grep -aiE "calihome|calibrate|homeEncoder|innerEncoder" $L | tail -12
