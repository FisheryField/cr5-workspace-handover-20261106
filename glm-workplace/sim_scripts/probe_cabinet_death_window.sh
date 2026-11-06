#!/bin/sh
# 只读：截取 14:13:55~14:15:00 原始日志窗口 + 死亡前后
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
S=$(grep -n '2026-10-12 14:13:5' $LOG | head -n 1 | cut -d: -f1)
E=$(grep -n '2026-10-12 14:15:0' $LOG | head -n 1 | cut -d: -f1)
echo "window lines $S..$E"
sed -n "${S},${E}p" $LOG | grep -vE 'PoseTrace|RealtimeHeartbeat|writeJsonFile|Record Run time' | head -c 16000
echo
echo '===== tail: last 12 lines before process restart marker ====='
R=$(grep -n 'create shm success' $LOG | tail -n 2 | head -n 1 | cut -d: -f1)
sed -n "$((R-14)),$((R+1))p" $LOG
echo done
