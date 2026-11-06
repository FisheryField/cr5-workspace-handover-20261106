#!/bin/sh
# P9 直发取证：控制器主日志三个时间窗（10-13）的 nextPos 规划值变化 + 报警/错误行
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== log info ==="
ls -l "$LOG"
echo
echo "=== W1 v14q P9直发+迟到落点窗口 10:09:57 - 10:11:41 (nextPos 变化行) ==="
grep -a -E '10:09:5[7-9]|10:10:|10:11:[0-4]' "$LOG" | grep -a 'gRobotAxisMove.nextPos' | awk '{p=index($0,"nextPos"); v=substr($0,p); if (v!=last) {print; last=v}}'
echo
echo "=== W1b 同窗 报警/错误/命令行 ==="
grep -a -E '10:09:5[7-9]|10:10:|10:11:[0-4]' "$LOG" | grep -a -E 'logServoError|AlarmSysSetBit|error|Error|MovL|MOVL|recv|Recv|cmd' | tail -60
echo
echo "=== W2 v14u P9直发 11:05:09 - 11:06:59 (nextPos 变化行) ==="
grep -a -E '11:05:|11:06:' "$LOG" | grep -a 'gRobotAxisMove.nextPos' | awk '{p=index($0,"nextPos"); v=substr($0,p); if (v!=last) {print; last=v}}'
echo
echo "=== W2b 同窗 报警/错误/命令行 ==="
grep -a -E '11:05:|11:06:' "$LOG" | grep -a -E 'logServoError|AlarmSysSetBit|error|Error|MovL|MOVL|recv|Recv|cmd' | tail -60
echo
echo "=== W3 v14v P9超时+回退+迟到落点 11:38:31 - 11:42:35 (nextPos 变化行) ==="
grep -a -E '11:38:|11:39:|11:4[01]:|11:42:[0-3]' "$LOG" | grep -a 'gRobotAxisMove.nextPos' | awk '{p=index($0,"nextPos"); v=substr($0,p); if (v!=last) {print; last=v}}'
echo
echo "=== W3b 同窗 报警/错误/命令行 ==="
grep -a -E '11:38:|11:39:|11:4[01]:|11:42:[0-3]' "$LOG" | grep -a -E 'logServoError|AlarmSysSetBit|error|Error|MovL|MOVL|recv|Recv|cmd' | tail -60
echo
echo "=== done ==="
