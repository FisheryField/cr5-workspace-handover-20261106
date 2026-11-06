#!/bin/sh
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 含 sdo 的日志行（全部）==="
grep -a -o '\[[0-9-]* [0-9:.]*\][^[]\{0,200\}sdo[^[]\{0,200\}' $L 2>/dev/null | head -40
echo
echo "=== 含 readServoParams / modifyServoParams 的行 ==="
grep -a -o '\[[0-9-]* [0-9:.]*\][^[]\{0,160\}\(readServoParams\|modifyServoParams\|servoParams\|driverParams\)[^[]\{0,160\}' $L 2>/dev/null | tail -20
echo
echo "=== 16:00 之后的 POST 请求 ==="
grep -a -o '\[2026-09-23 1[6-9]:[0-9:.]*\][^[]\{0,140\}POST uri[^[]\{0,60\}' $L 2>/dev/null | tail -25
echo
echo "=== 现在时间 ==="; date
