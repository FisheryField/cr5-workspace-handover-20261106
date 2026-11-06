#!/bin/sh
PID=$(pidof codesyscontrol)
OUT=/tmp/memdump2
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
  echo "$line" | grep -q '\[stack:' && continue
  start=${addr%-*}
  end=${addr#*-}
  s=$((0x$start))
  e=$((0x$end))
  sz=$((e-s))
  [ $sz -le 0 ] && continue
  [ $sz -gt 16777216 ] && continue
  tot=$((tot+sz))
  if [ $tot -gt 67108864 ]; then echo "cap reached"; break; fi
  i=$((i+1))
  dd if=/proc/$PID/mem of=$OUT/r$i.bin bs=4096 skip=$((s/4096)) count=$((sz/4096)) 2>/dev/null
  echo "$i $addr $perm $sz" >> $OUT/manifest.txt
done < $OUT/maps.txt
echo "regions=$i"
cat $OUT/manifest.txt
du -sk $OUT
cd /tmp && tar czf /tmp/memdump2.tgz memdump2
ls -la /tmp/memdump2.tgz
echo "=== gcontrol maps (rw, no stack) ==="
grep -E ' rw' /proc/$(pidof gcontrol)/maps | grep -v '\[stack:' | head -30
