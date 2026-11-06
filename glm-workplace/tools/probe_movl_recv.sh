#!/bin/sh
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo "=== log.18+log.17+log.16: 所有 recv 命令行 (11:33-11:40) ==="
grep -a -E 'recv = (MovL|JointMovJ|EnableRobot|Sync|RelMov|ServoJ|Start|Stop)' "$D/log.18" "$D/log.17" "$D/log.16" | grep -a -E 'MovL|JointMovJ' | tail -60
echo
echo "=== 所有 movl 返回值 ==="
grep -a 'func = movl' "$D/log.18" "$D/log.17" "$D/log.16" | tail -20
echo
echo "=== panelJog / drag / jog 事件 (log.16..log.12) ==="
grep -a -E 'panelJog|dragMode=1|StartDrag|FreeDrag|jog' "$D/log.16" "$D/log.15" "$D/log.14" "$D/log.13" "$D/log.12" | grep -a -E 'panelJog controlMode|StartDrag|dragMode=1' | tail -40
echo "=== done ==="
