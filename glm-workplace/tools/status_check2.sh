#!/bin/sh
# 只读：确认日志文件状态 + 0x7c 报警上下文 + 版本行的正确抓法
echo "===== log 文件大小/时间 ====="
ls -la /dobot/userdata/CR5_sys_files/project/logs/all/ 2>/dev/null | head -10
echo
echo "===== settVersion（不区分大小写） ====="
grep -ai "settversion" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -14
echo
echo "===== 本次开机以来的版本行（codesys 启动期） ====="
grep -a "3.1.5.0\|3.5.6" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -10
echo
echo "===== 0x7c 报警上下文（前后各 2 行） ====="
grep -an -B2 -A2 "index=0x7c" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -30
echo
echo "===== 最近报警全量（AlarmSysSetBit 最近 20 条，含 isOn=0） ====="
grep -a "AlarmSysSetBit" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -20
