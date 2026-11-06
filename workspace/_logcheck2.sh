#!/bin/sh
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 最近的相关日志 ==="
grep -aoE '.{0,30}(SDOWRCount|sdo read|start read sdo|pack addr|is error|parseAndReq).{0,110}' $L 2>/dev/null | tail -20
