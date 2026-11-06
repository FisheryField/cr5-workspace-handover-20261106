#!/bin/sh
# 清掉所有遗留
for p in $(ps | grep tcpdump | grep -v grep | awk '{print $1}'); do kill -9 $p 2>/dev/null; done
sleep 1
echo "=== 剩下 ==="; ps | grep tcpdump | grep -v grep
echo
echo "=== 测 BPF 语法 ==="
/mToolServer/tcpdump -i eth0 -s 0 -c 3 'ether proto 0x88a4' 2>&1 | head -6
echo "--- 带长度过滤 ---"
/mToolServer/tcpdump -i eth0 -s 0 -c 3 'ether proto 0x88a4 and not len 1111' 2>&1 | head -6
echo "--- 只按长度 ---"
/mToolServer/tcpdump -i eth0 -s 0 -c 3 'not len 1111' 2>&1 | head -6
