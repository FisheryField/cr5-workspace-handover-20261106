PID=376
echo "=== maps (按大小 top12) ==="
while read -r line; do
  set -- $line
  range=$1
  start=${range%%-*}; end=${range##*-}
  sz=$(( (0x$end - 0x$start) / 1024 ))
  echo "$sz $start $2 $6"
done < /proc/$PID/maps | sort -rn | head -12
echo
echo "=== 在内存里搜符号名 ==="
PAT="IoConfig_Globals.a1.config.write"
FOUND=0
while read -r line; do
  set -- $line
  range=$1; perm=$2
  case "$perm" in r*) ;; *) continue;; esac
  start=${range%%-*}; end=${range##*-}
  sz=$(( 0x$end - 0x$start ))
  [ $sz -lt 65536 ] && continue
  [ $sz -gt 33554432 ] && continue
  off=$(dd if=/proc/$PID/mem bs=4096 skip=$((0x$start/4096)) count=$((sz/4096)) 2>/dev/null | grep -abo "$PAT" | head -1 | cut -d: -f1)
  if [ -n "$off" ]; then
    addr=$((0x$start + off))
    echo "  ★ 命中 0x$(printf %x $addr)   区域 $range $perm $6"
    FOUND=$((FOUND+1))
    [ $FOUND -ge 3 ] && break
  fi
done < /proc/$PID/maps
echo "命中 $FOUND 处"
