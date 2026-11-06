#!/bin/sh
echo "=== 控制器上与 22000/29999/30003-30006 相关的连接 ==="
netstat -tn 2>/dev/null | grep -E ':(22000|29999|3000[3-6])\b' | head -30
echo
echo "=== 监听状态 ==="
netstat -lnt 2>/dev/null | grep -E ':(22000|29999)\b'
echo
echo "=== 谁在用 22000（按来源 IP 统计）==="
netstat -tn 2>/dev/null | grep ':22000' | awk '{print $5}' | sort | uniq -c | sort -rn | head -10
