#!/bin/sh
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 最近 60 秒内出现的相关日志 ==="
grep -aoE '.{0,40}(readServoParams|parseAndReq|exitSDOWRThd|start read sdo|start write sdo|pack addr|is error|SDOWRCount|servoParams.json).{0,110}' $L 2>/dev/null | tail -25
echo
echo "=== 关节值 ==="
