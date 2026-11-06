#!/bin/sh
# 只读取证：控制器日志里最近一次使能/错误记录 + codesys 日志尾部 + 进程状态
echo "== all/log tail: enable/disable/error =="
tail -c 3000000 /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | strings | grep -aiE 'enable|disable|error|estop|emergency' | tail -30
echo
echo "== codesys log tail (grep -ao style) =="
tail -c 3000000 /dobot/userdata/CR5_sys_files/project/logs/codesys/log 2>/dev/null | grep -aoE '.{0,80}(Error|error|Init|Boot).{0,80}' | tail -20
echo
echo "== processes =="
ps | grep -aE 'codesyscontrol|gcontrol' | grep -av grep
echo
echo "== uptime/net =="
uptime
netstat -an 2>/dev/null | grep -aE '30005|29999|22000' | head -8
