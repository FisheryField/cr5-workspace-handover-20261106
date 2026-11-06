date; cat /proc/uptime
ps | grep -E "codesys" | grep -v grep
echo '=== 试 /properties/driverParams（伺服驱动参数端点）==='
for M in POST GET; do
  echo "--- $M ---"
  wget -qO- --post-data='{}' --header='Content-Type: application/json' http://127.0.0.1:22000/properties/driverParams 2>&1 | head -c 400
  echo
  break
done
echo
echo '=== 试完后再看日志有没有 sdo 记录 ==='
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
for k in "sdo read" "sdo write" "sdo read fail"; do printf "  %-16s %s\n" "$k" "$(grep -a -c "$k" "$LOG" 2>/dev/null)"; done
echo
echo '=== 当前 homeEncoder.json 末条 ==='
grep -oE "\"time\": \"[0-9:]+\"" /dobot/userdata/project/settings/function/homeEncoder.json 2>/dev/null | tail -1
