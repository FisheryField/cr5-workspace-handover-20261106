#!/bin/sh
PID=$(pidof codesyscontrol)
BASE=$(grep -i 'libdataSvr' /proc/$PID/maps | head -1 | cut -d'-' -f1)
B=$((0x$BASE))
printf "SDOWRCount      = "; dd if=/proc/$PID/mem bs=1 skip=$((B+0x277edc)) count=4 2>/dev/null | od -An -td4
printf "IsExistSDOWRThd = "; dd if=/proc/$PID/mem bs=1 skip=$((B+0x277ed1)) count=1 2>/dev/null | od -An -tu1
echo "--- AllSDOWRInfo 前 96 字节（非零即命中）---"
dd if=/proc/$PID/mem bs=1 skip=$((B+0x285fe0)) count=96 2>/dev/null | od -A d -tx1
echo "--- 日志 sdo read ---"
grep -aoE 'sdo read,slave=[0-9]+,index=[^,]*,[^,]*,[^.]*' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -5
echo "--- 日志 is error ---"
grep -aoE 'the key [^ ]* is error' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -5
