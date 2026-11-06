#!/bin/sh
PID=$(pidof codesyscontrol)
echo "=== 0x75630BB4 起 96 字节 (6 个 double, 间距 16) ==="
dd if=/proc/$PID/mem bs=1 skip=$((0x75630BB4)) count=96 2>/dev/null | od -A d -t f8
echo
echo "=== 再取一次，看是否变化 ==="
sleep 3
dd if=/proc/$PID/mem bs=1 skip=$((0x75630BB4)) count=96 2>/dev/null | od -A d -t f8
echo
echo "=== 顺带看 +96 之后 64 字节（相邻字段）==="
dd if=/proc/$PID/mem bs=1 skip=$((0x75630BB4+96)) count=64 2>/dev/null | od -A d -t f8
