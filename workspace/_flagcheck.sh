#!/bin/sh
PID=$(pidof codesyscontrol)
echo "=== libdataSvr 在 maps 里的映射 ==="
grep -i 'libdataSvr' /proc/$PID/maps
echo
echo "=== 取基址并读三个全局量 ==="
BASE=$(grep -i 'libdataSvr' /proc/$PID/maps | head -1 | cut -d'-' -f1)
echo "base=$BASE"
B=$((0x$BASE))
for spec in "IsExistSDOWRThd:0x277ed1:1" "SDOWRThd:0x277ed4:4" "SDOWRCount:0x277edc:4" "AllSDOWRStatus:0x277ed8:4"; do
  N=${spec%%:*}; rest=${spec#*:}
  OFF=${rest%%:*}; SZ=${rest##*:}
  ADDR=$((B + OFF))
  printf "%-18s off=%-10s addr=0x%x  = " "$N" "$OFF" "$ADDR"
  dd if=/proc/$PID/mem bs=1 skip=$ADDR count=$SZ 2>/dev/null | od -An -tx1 | tr -d '\n'
  echo
done
