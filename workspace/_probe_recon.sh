#!/bin/sh
echo "=== /tmp 下的工具 ==="
ls -la /tmp/*.so /tmp/ecat* /tmp/slave* /tmp/*.bin 2>/dev/null
echo
echo "=== 找所有可能的总线探针 ==="
find / -xdev -type f \( -name 'ecat*' -o -name 'slaveinfo*' -o -name '*soem*' \) 2>/dev/null | head -20
echo
echo "=== ecat_zero 用法（无参数）==="
/tmp/ecat_zero 2>&1 | head -20
echo
echo "=== 有没有编译器 ==="
which gcc cc make 2>/dev/null
echo
echo "=== 当前进程 ==="
ps | grep -E 'codesyscontrol|gcontrol' | grep -v grep
echo
echo "=== 网口 ==="
ip -o link 2>/dev/null | head -10
