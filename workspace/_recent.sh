#!/bin/sh
echo "=== /tmp 全部 ==="
ls -la /tmp
echo
echo "=== 最近 3 小时内被修改的文件（排除 /proc /sys /tmp）==="
find / -xdev -mmin -180 -type f 2>/dev/null | grep -vE '^/(proc|sys|tmp|dev|run)/' | head -40
echo
echo "=== /tmp 下最近 3 小时 ==="
find /tmp -mmin -180 -type f 2>/dev/null | head -20
echo
echo "=== slave.json 尾部（看还有什么字段）==="
tail -c 800 /tmp/slave.json
