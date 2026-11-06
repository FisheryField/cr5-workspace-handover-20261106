#!/bin/sh
echo "=== host ==="; hostname; date
echo "=== /dobot 顶层 ==="
ls -la /dobot 2>/dev/null
echo "=== 找 EtherCAT/ENI 组态文件 ==="
find /dobot /root /usr/local /opt /etc -maxdepth 6 \( -iname '*eni*' -o -iname '*ethercat*' -o -iname '*ecat*' -o -iname '*.esx' -o -iname '*.xml' \) 2>/dev/null | head -60
echo "=== CODESYS 工程目录 ==="
find /dobot -maxdepth 5 -iname '*project*' -o -maxdepth 5 -iname '*.app' 2>/dev/null | head -30
echo "=== 运行中的进程 ==="
ps | grep -Ei 'codesys|gcontrol|datasvr' | grep -v grep
echo "=== 谁在监听 ==="
netstat -lntp 2>/dev/null | head -25
