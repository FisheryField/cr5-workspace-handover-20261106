#!/bin/sh
# probe_powerup_pin_1013.sh — 收口探针：本体电压最新值/SafeIO 报错历史/服务端口（只读）
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo "===== [1] 今天所有 uiBodyVolt / bBodyPowerFlag 行（本体电压轨迹） ====="
grep -n 'uiBodyVolt' "$LOG" 2>/dev/null | grep '2026-10-13' | tail -n 12

echo ""
echo "===== [2] 今天 getSafeIO_error_code 出现次数与最后 5 条 ====="
grep -c 'getSafeIO_error_code' "$LOG" 2>/dev/null
grep -n 'getSafeIO_error_code' "$LOG" 2>/dev/null | grep '2026-10-13' | tail -n 5

echo ""
echo "===== [3] 今天 g_isRobotPowerOn / gPowerDown 行 ====="
grep -nE 'gPowerDown|g_isRobotPowerOn' "$LOG" 2>/dev/null | grep '2026-10-13' | tail -n 8

echo ""
echo "===== [4] codesys 日志尾部 15 行 ====="
ls -t /dobot/userdata/CR5_sys_files/project/logs/codesys/ 2>/dev/null | head -n 3
tail -n 15 /dobot/userdata/CR5_sys_files/project/logs/codesys/$(ls -t /dobot/userdata/CR5_sys_files/project/logs/codesys/ 2>/dev/null | head -n 1) 2>/dev/null

echo ""
echo "===== [5] 主控服务端口监听状态 ====="
netstat -tln 2>/dev/null | grep -E ':(22000|29999|30003|30004)' | head -n 8

echo ""
echo "===== [6] 今天 09:18:40 之后的 alarm/伺服错误行（之后有没有新报警） ====="
awk '/2026-10-13 09:18:4/,0' "$LOG" 2>/dev/null | grep -iE 'alarm|servo[1-6] error|error' | head -n 12

echo "===== [7] 完 ====="
