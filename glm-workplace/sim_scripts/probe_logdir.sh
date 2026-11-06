#!/bin/sh
echo '=== 日志目录 ==='
ls -la /dobot/userdata/CR5_sys_files/project/logs/all/ 2>&1 | tail -15
echo '=== 备选目录 ==='
ls -la /dobot/userdata/project/logs/all/ 2>&1 | tail -10
echo '=== 主日志头尾 ==='
F=/dobot/userdata/CR5_sys_files/project/logs/all/log
wc -c "$F" 2>&1
tail -c 800 "$F" 2>&1
