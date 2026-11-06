#!/bin/sh
PID=$(pidof codesyscontrol)
dd if=/proc/$PID/mem of=/tmp/r15_a.bin bs=4096 skip=$((0x75600000/4096)) count=67 2>/dev/null
sleep 4
dd if=/proc/$PID/mem of=/tmp/r15_b.bin bs=4096 skip=$((0x75600000/4096)) count=67 2>/dev/null
ls -la /tmp/r15_a.bin /tmp/r15_b.bin
echo "=== 两次是否相同 ==="
cmp /tmp/r15_a.bin /tmp/r15_b.bin && echo "完全相同" || echo "有差异"
cd /tmp && tar czf /tmp/r15.tgz r15_a.bin r15_b.bin
ls -la /tmp/r15.tgz
