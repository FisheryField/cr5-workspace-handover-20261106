#!/bin/sh
L=/dobot/userdata/CR5_sys_files/project/logs/codesys/log
echo "=== log size ==="; ls -la $L
echo "=== SDO / 16# 相关行（去重前 80）==="
grep -a -n "SDO\|16#\|SM2\|SM3\|PDO" $L 2>/dev/null | head -80
echo "=== 统计 ==="
grep -ac "SDO" $L
