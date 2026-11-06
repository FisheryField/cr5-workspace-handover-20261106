LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo '=== 本次开机后的 sdo / encoder 相关 ==='
awk '/2026-09-23 11:3[7-9]|2026-09-23 11:4[0-9]/' "$LOG" 2>/dev/null | grep -a -iE "sdo|encoder|calihome|servoParam" | head -20
echo
echo '=== 全日志里 sdo 相关计数 ==='
for k in "sdo read" "sdo write" "sdo read fail" "init sdo index map" "SDOWRCount"; do
  printf "  %-22s %s\n" "$k" "$(grep -a -c "$k" "$LOG" 2>/dev/null)"
done
echo
echo '=== 本次开机 settVersion ==='
grep -a -A14 "settVersion#4492" "$LOG" 2>/dev/null | tail -16
