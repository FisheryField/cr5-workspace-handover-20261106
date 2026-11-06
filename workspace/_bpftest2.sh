#!/bin/sh
echo "=== 测 ether proto + less ==="
/mToolServer/tcpdump -i eth0 -s 0 -c 2 'ether proto 0x88a4 and less 1100' 2>&1 | head -5
echo
echo "=== 测 greater 也行吗 ==="
/mToolServer/tcpdump -i eth0 -s 0 -c 2 'ether proto 0x88a4 and (less 1100 or greater 1130)' 2>&1 | head -5
