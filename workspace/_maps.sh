#!/bin/sh
PID=$(pidof codesyscontrol)
echo "codesyscontrol pid = $PID"
echo "=== rw 区域一览（按大小排序）==="
awk '{ split($1,a,"-"); sz=(strtonum("0x" a[2])-strtonum("0x" a[1]))/1024; if ($2 ~ /rw/) printf "%10d KB  %s  %s\n", sz, $1, $6 }' /proc/$PID/maps 2>/dev/null | sort -rn | head -25
echo "=== 总计 ==="
awk '{ split($1,a,"-"); sz=(strtonum("0x" a[2])-strtonum("0x" a[1])); if ($2 ~ /rw/) t+=sz } END { printf "rw total = %.1f MB\n", t/1048576 }' /proc/$PID/maps 2>/dev/null
echo "=== 前 12 行原始 maps ==="
head -12 /proc/$PID/maps
