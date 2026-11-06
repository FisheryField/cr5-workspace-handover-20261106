#!/bin/sh
chmod +x /tmp/ecat_zero
ls -la /tmp/ecat_zero
echo "=== 确认网口 ==="
cat /proc/net/dev | head -8
