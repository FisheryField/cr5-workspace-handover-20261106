#!/bin/sh
echo "=== 磁盘空间 ==="
df -h 2>/dev/null | head -12
echo
echo "=== tcpdump 可用性 ==="
/mToolServer/tcpdump -D 2>&1 | head -8
echo
echo "=== 现在时间 ==="
date
