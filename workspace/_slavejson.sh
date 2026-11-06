#!/bin/sh
echo "=== slave.json 头部 ==="
head -c 1500 /tmp/slave.json
echo
echo "..."
echo "=== 结构概览 ==="
head -c 200000 /tmp/slave.json | tr ',' '\n' | grep -oE '"[A-Za-z_]+"[[:space:]]*:' | sort | uniq -c | sort -rn | head -30
