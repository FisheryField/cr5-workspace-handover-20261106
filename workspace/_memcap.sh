#!/bin/sh
PID=$(pidof codesyscontrol)
echo "pid=$PID"
OUT=/tmp/memdump
rm -rf $OUT
mkdir -p $OUT
cp /proc/$PID/maps $OUT/maps.txt
i=0
tot=0
while read line; do
  set -- $line
  addr=$1
  perm=$2
  case "$perm" in rw*) ;; *) continue ;; esac
  start=${addr%-*}
  end=${addr#*-}
  s=$((0x$start))
  e=$((0x$end))
  sz=$((e-s))
  [ $sz -le 0 ] && continue
  [ $sz -gt 16777216 ] && continue
  tot=$((tot+sz))
  if [ $tot -gt 50331648 ]; then echo "达到总量上限，停止"; break; fi
  i=$((i+1))
  dd if=/proc/$PID/mem of=$OUT/r$i.bin bs=4096 skip=$((s/4096)) count=$((sz/4096)) 2>/dev/null
  echo "$i $addr $perm $sz" >> $OUT/manifest.txt
done < $OUT/maps.txt
echo "regions=$i"
echo "--- manifest ---"
cat $OUT/manifest.txt
du -sk $OUT
cd /tmp && tar czf /tmp/memdump.tgz memdump
ls -la /tmp/memdump.tgz
