#!/bin/sh
PID=$(pidof codesyscontrol)
echo "pid=$PID"
echo "=== r15: 0x75630B80 起 192 字节, 按 double 打印 ==="
dd if=/proc/$PID/mem bs=1 skip=$((0x75630B80)) count=192 2>/dev/null | od -A d -t f8
echo
echo "=== 同上, 按 int32 打印 ==="
dd if=/proc/$PID/mem bs=1 skip=$((0x75630B80)) count=192 2>/dev/null | od -A d -t d4
echo
echo "=== r2: 0x0027d000+154300 起 256 字节, int32 ==="
dd if=/proc/$PID/mem bs=1 skip=$((0x27d000+154300)) count=256 2>/dev/null | od -A d -t d4
