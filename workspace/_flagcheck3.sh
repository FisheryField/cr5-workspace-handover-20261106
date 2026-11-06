#!/bin/sh
PID=$(pidof codesyscontrol)
BASE=$(grep -i 'libdataSvr' /proc/$PID/maps | head -1 | cut -d'-' -f1)
B=$((0x$BASE))
echo "=== 全部 libdataSvr 映射 ==="
grep -i 'libdataSvr' /proc/$PID/maps
echo "=== 计算出的地址是否落在映射内 ==="
echo "IsExistSDOWRThd  -> 0x$(printf %x $((B+0x277ed1)))"
echo "AllSDOWRInfo    -> 0x$(printf %x $((B+0x285fe0)))"
echo "=== 读值 ==="
for spec in "IsExistSDOWRThd:0x277ed1:1" "SDOWRCount:0x277edc:4"; do
  N=${spec%%:*}; rest=${spec#*:}; OFF=${rest%%:*}; SZ=${rest##*:}
  printf "%-18s = " "$N"
  dd if=/proc/$PID/mem bs=1 skip=$((B+OFF)) count=$SZ 2>&1 | od -An -tx1 | tr -d '\n'
  echo
done
echo "=== AllSDOWRInfo 前 128 字节 ==="
dd if=/proc/$PID/mem bs=1 skip=$((B+0x285fe0)) count=128 2>/dev/null | od -A d -tx1
echo "=== 日志：有无 sdo read ==="
grep -aoE 'sdo read,slave=[0-9]+,index=[^,]*,[^,]*,[^.]*' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -8
