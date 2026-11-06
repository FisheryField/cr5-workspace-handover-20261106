#!/bin/sh
# 在主控本地采样关节值（读 codesyscontrol 的 /proc/pid/mem），不占网络
PID=$(pidof codesyscontrol)
ADDR=$((0x75630BB4))
RAW=/tmp/ab_raw.bin
TS=/tmp/ab_ts.txt
: > $RAW
: > $TS
rm -f /tmp/ab_stop /tmp/ab_done.txt
echo "start pid=$PID addr=$ADDR hex=0x75630BB4 uptime=$(cat /proc/uptime)" > /tmp/ab_meta.txt
n=0
while [ $n -lt 18000 ]; do
  [ -f /tmp/ab_stop ] && break
  read UP rest < /proc/uptime
  echo "$UP" >> $TS
  dd if=/proc/$PID/mem bs=1 skip=$ADDR count=96 >> $RAW 2>/dev/null
  n=$((n+1))
  usleep 100000
done
echo "done n=$n uptime=$(cat /proc/uptime)" >> /tmp/ab_meta.txt
