LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo '=== 控制器日志里有没有真正的 SDO 读写记录 ==='
grep -a -c "sdo read" "$LOG" 2>/dev/null
grep -a -c "sdo write" "$LOG" 2>/dev/null
echo '--- 抽样 ---'
grep -a -oE "sdo (read|write)[^\"]{0,90}" "$LOG" 2>/dev/null | tail -20
echo
echo '=== SDOWRCount / IsWriteFromFile / sdo index map ==='
grep -a -oE "(SDOWRCount = [0-9]+|IsWriteFromFile=[a-z]+|init sdo index map)" "$LOG" 2>/dev/null | sort | uniq -c | tail -5
echo
echo '=== 11:02 那次标零的完整序列 ==='
awk '/2026-09-23 11:02:1[5-9]/,/2026-09-23 11:02:2[0-5]/' "$LOG" 2>/dev/null | grep -a -E "calibrate|calihome|encoder|SDO|sdo|writeJson" | head -20
