#!/bin/sh
# 只读：查最近的运动指令接收/拒绝记录（JointMovJ/MovL/错误码）
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== tail 运动指令相关（最近120条命中）==="
grep -a -E 'JointMovJ|MovL#|the type of params|40006|40004|8612|gRobotAxisMove|MoveJ#|MoveL#' "$LOG" | tail -120
echo "=== log 末 15 行（看时钟）==="
tail -15 "$LOG"
