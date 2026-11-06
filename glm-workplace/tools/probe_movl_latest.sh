#!/bin/sh
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo "=== 最近的 JointMovJ 收令（含193）与返回 ==="
grep -a 'recv = JointMovJ' "$D/log" "$D/log.1" "$D/log.2" "$D/log.3" 2>/dev/null | tail -12
echo
grep -a 'func = jointmovj' "$D/log" "$D/log.1" "$D/log.2" "$D/log.3" 2>/dev/null | tail -12
echo "=== 同窗错误 ==="
grep -a -E '\[error\]|3000|limit|Limit' "$D/log.1" 2>/dev/null | tail -15
echo "=== done ==="
