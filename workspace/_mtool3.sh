#!/bin/sh
L=/mToolServer/mToolServer.log
echo "=== 所有出现过的 URI / 路由 ==="
grep -a -oE '\[http_server\.cpp@[A-Za-z_]+\(\)#[0-9]+\][^\"]{0,80}' $L 2>/dev/null | sed 's/.*]//' | sort | uniq -c | sort -rn | head -40
echo
echo "=== 所有 http_server 函数名 ==="
grep -a -oE 'http_server\.cpp@[A-Za-z_0-9]+' $L 2>/dev/null | sort | uniq -c | sort -rn
echo
echo "=== 含 uri / path / route 的行 ==="
grep -a -iE 'uri|route|endpoint|/update/|/get|/set|/read|/write' $L 2>/dev/null | grep -v FoE | tail -30
echo
echo "=== 全部 cpp 文件名（看模块划分）==="
grep -a -oE '[a-z_]+\.cpp' $L 2>/dev/null | sort | uniq -c | sort -rn | head -25
