#!/bin/sh
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 最近日志（关键行）==="
grep -aoE '.{0,20}(SDOWRCount|sdo read|sdo write|start read sdo|start write sdo|pack addr|is error|parseAndReqGet|parseAndReqSet).{0,110}' $L 2>/dev/null | tail -18
