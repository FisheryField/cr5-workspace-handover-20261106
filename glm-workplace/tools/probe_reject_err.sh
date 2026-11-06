#!/bin/sh
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo "=== 15:54 前后错误/拒绝 ==="
grep -a -E 'error|Error|40001|3000|limit|Limit|干涉|reject' "$D/log" "$D/log.1" "$D/log.2" 2>/dev/null | tail -30
echo
echo "=== 最近 recv 运动指令 ==="
grep -a -E 'recv = (MotionJ|MoveJ|JointMovJ|MotionL|MovL)' "$D/log" "$D/log.1" 2>/dev/null | tail -10
echo "=== done ==="
