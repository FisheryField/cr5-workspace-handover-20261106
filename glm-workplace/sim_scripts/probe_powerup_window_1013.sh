#!/bin/sh
# probe_powerup_window_1013.sh — 开机窗口日志深挖：报警/电压/伺服初始化结果（只读）
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo "===== [1] 开机窗口 09:15-09:22 全部 error/warn/alarm/volt 行 ====="
grep -nE '^\[2026-10-13 09:(1[5-9]|2[0-2])' "$LOG" 2>/dev/null | grep -iE 'error|warn|alarm|volt|servo|power|ethercat|op mode|io board|exception' | head -n 60

echo ""
echo "===== [2] 09:15 之后带电压关键词的所有行（不限级别） ====="
grep -nE '^\[2026-10-13 09:(1[5-9]|2[0-9])' "$LOG" 2>/dev/null | grep -iE 'volt|207|220|under|over' | head -n 30

echo ""
echo "===== [3] 开机后前 60 行原始日志（伺服初始化叙事） ====="
grep -n '^\[2026-10-13 09:1' "$LOG" 2>/dev/null | head -n 60

echo ""
echo "===== [4] WorkTimeRec.json（伺服计数器再读一次，对比冻结） ====="
cat /dobot/userdata/project/settings/workTime/WorkTimeRec.json 2>/dev/null

echo ""
echo "===== [5] 其它日志目录（找 servo 专属日志） ====="
ls -lt /dobot/userdata/CR5_sys_files/project/logs/ 2>/dev/null | head -n 15

echo ""
echo "===== [6] dmesg 尾部（电源/总线硬件层） ====="
dmesg 2>/dev/null | tail -n 25

echo "===== [7] 完 ====="
