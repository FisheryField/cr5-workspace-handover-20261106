LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo '=== 探测前：sdo 相关计数 ==='
for k in "sdo read" "sdo write" "sdo read fail"; do printf "  %-16s %s\n" "$k" "$(grep -a -c "$k" "$LOG" 2>/dev/null)"; done
echo
echo '=== POST /properties/driverParams (空 JSON) ==='
wget -qO- --post-data='{}' --header='Content-Type: application/json' http://127.0.0.1:22000/properties/driverParams 2>&1 | head -c 1200
echo; echo
echo '=== GET /properties/driverParams ==='
wget -qO- http://127.0.0.1:22000/properties/driverParams 2>&1 | head -c 600
echo; echo
echo '=== 试探其它 driver/servo 端点 ==='
for u in /properties/servoParams /servo/driverParams /settings/driverParams /interface/readCurrentEncoder /properties/controllerType /connection/state; do
  printf "  %-34s " "$u"
  wget -qO- --post-data='{}' --header='Content-Type: application/json' "http://127.0.0.1:22000$u" 2>&1 | head -c 160
  echo
done
echo
echo '=== 探测后：sdo 相关计数（若变了说明触发了 SDO 路径）==='
for k in "sdo read" "sdo write" "sdo read fail"; do printf "  %-16s %s\n" "$k" "$(grep -a -c "$k" "$LOG" 2>/dev/null)"; done
echo
echo '=== servoParams.json 是否被创建 ==='
ls -la /dobot/userdata/project/settings/function/servoParams.json 2>/dev/null || echo '(仍不存在)'
