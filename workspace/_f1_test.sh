#!/bin/sh
# 把断电前的 f1 写回控制器共享内存：page132 偏移 0xE2C + 40*i
PID=$(pidof codesyscontrol | awk '{print $1}')
echo "pid=$PID"
[ -n "$PID" ] || { echo NO_PID; exit 2; }
SEL=$(grep "SYSVe901001b" /proc/$PID/maps | head -1)
BASEHEX=$(echo "$SEL" | cut -d- -f1)
B=$((0x$BASEHEX))
echo "base=0x$BASEHEX"
P132=$((B+132*4096))
P133=$((B+133*4096))

echo "=== [1] 写之前 ==="
echo "-- 位姿 page133+0x04 --"
dd if=/proc/$PID/mem bs=1 skip=$((P133+4)) count=24 2>/dev/null | od -A n -t f4
echo "-- page132 f0/f1 --"
for i in 0 1 2 3 4 5; do
  printf "  轴%d  f0=" $((i+1))
  dd if=/proc/$PID/mem bs=1 skip=$((P132+0xE24+40*i)) count=4 2>/dev/null | od -A n -t f4 | tr -d " 
"
  printf "   f1="
  dd if=/proc/$PID/mem bs=1 skip=$((P132+0xE2C+40*i)) count=4 2>/dev/null | od -A n -t f4 | tr -d " 
"
  echo
done

echo "=== [2] 备份原 256 字节 ==="
dd if=/proc/$PID/mem of=/tmp/f1_backup.bin bs=1 skip=$((P132+0xE20)) count=256 2>/dev/null
ls -la /tmp/f1_backup.bin

echo "=== [3] 写回断电前的 f1 ==="
printf '\000\000\214\301' | dd of=/proc/$PID/mem bs=1 seek=$((P132+0xE2C+0)) conv=notrunc 2>/dev/null
echo "  轴1 <- -17.5"
printf '\000\300\132\104' | dd of=/proc/$PID/mem bs=1 seek=$((P132+0xE2C+40)) conv=notrunc 2>/dev/null
echo "  轴2 <- 875.0"
printf '\000\000\214\102' | dd of=/proc/$PID/mem bs=1 seek=$((P132+0xE2C+80)) conv=notrunc 2>/dev/null
echo "  轴3 <- 70.0"
printf '\000\000\304\102' | dd of=/proc/$PID/mem bs=1 seek=$((P132+0xE2C+120)) conv=notrunc 2>/dev/null
echo "  轴4 <- 98.0"
printf '\146\146\076\102' | dd of=/proc/$PID/mem bs=1 seek=$((P132+0xE2C+160)) conv=notrunc 2>/dev/null
echo "  轴5 <- 47.6"
printf '\146\146\366\101' | dd of=/proc/$PID/mem bs=1 seek=$((P132+0xE2C+200)) conv=notrunc 2>/dev/null
echo "  轴6 <- 30.8"

echo "=== [4] 立刻回读 f1（判断是否写住）==="
for i in 0 1 2 3 4 5; do
  printf "  轴%d  f1=" $((i+1))
  dd if=/proc/$PID/mem bs=1 skip=$((P132+0xE2C+40*i)) count=4 2>/dev/null | od -A n -t f4 | tr -d " 
"
  echo
done

sleep 3
echo "=== [5] 3 秒后 ==="
echo "-- 位姿 --"
dd if=/proc/$PID/mem bs=1 skip=$((P133+4)) count=24 2>/dev/null | od -A n -t f4
echo "-- f1 --"
for i in 0 1 2 3 4 5; do
  printf "  轴%d  f1=" $((i+1))
  dd if=/proc/$PID/mem bs=1 skip=$((P132+0xE2C+40*i)) count=4 2>/dev/null | od -A n -t f4 | tr -d " 
"
  echo
done

echo "=== [6] 进程状态 ==="
ps | grep codesyscontrol | grep -v grep || echo "!! codesyscontrol 已退出"
