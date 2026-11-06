ls -la /tmp/ecat_zero 2>/dev/null || echo "工具缺失"
echo
echo "轴   statusword   errorcode(0x603F)  mode(0x6061)  ctrl(0x6040)"
for s in 3 4 5 6 7 8; do
  sw=$(/tmp/ecat_zero rv $s 0x6041 0 2>&1 | tail -1 | sed 's/.*= //')
  ec=$(/tmp/ecat_zero rv $s 0x603F 0 2>&1 | tail -1 | sed 's/.*= //')
  md=$(/tmp/ecat_zero rv $s 0x6061 0 2>&1 | tail -1 | sed 's/.*= //')
  cw=$(/tmp/ecat_zero rv $s 0x6040 0 2>&1 | tail -1 | sed 's/.*= //')
  printf "%-4s %-12s %-18s %-13s %s\n" "$s" "${sw:-?}" "${ec:-?}" "${md:-?}" "${cw:-?}"
done
echo
echo "=== 控制器侧当前报警 ==="
wget -q -O - "http://127.0.0.1:22000/protocol/exchange" 2>/dev/null | head -c 400
echo
echo "=== 日志里的报警 ==="
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
tail -2000 $L | grep -aE "alarm|Alarm|ALARM|error|Error" | grep -avE "ALARMS:raw|alarm_io" | tail -15
