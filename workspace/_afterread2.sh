#!/bin/sh
echo "=== 主控侧：新文件 / 新日志 ==="
find /dobot /tmp -mmin -4 -type f 2>/dev/null | head -15
echo "--- sdo 行计数 ---"
grep -a -c 'sdo' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null
echo "--- 最近日志尾部 ---"
tail -c 600 /dobot/userdata/CR5_sys_files/project/logs/codesys/log 2>/dev/null | tr -d '\000' | tail -c 600
