PID=376
PAT="IoConfig_Globals.a1.config.write"
echo "=== 非栈的大映射 (top 20) ==="
while read -r line; do
  set -- $line
  range=$1
  case "$6" in *stack*) continue;; esac
  start=${range%%-*}; end=${range##*-}
  sz=$(( (0x$end - 0x$start) / 1024 ))
  echo "$sz $start $2 $6"
done < /proc/$PID/maps | sort -rn | head -20
echo
echo "=== 逐区测试是否含符号名 (>=64KB) ==="
while read -r line; do
  set -- $line
  range=$1; perm=$2
  case "$perm" in r*) ;; *) continue;; esac
  start=${range%%-*}; end=${range##*-}
  sz=$(( 0x$end - 0x$start ))
  [ $sz -lt 65536 ] && continue
  c=$(dd if=/proc/$PID/mem bs=4096 skip=$((0x$start/4096)) count=$((sz/4096)) 2>/dev/null | grep -ac "$PAT")
  [ "$c" != "0" ] && echo "  ★ 0x$start ($((sz/1024))KB) $perm $6  grep计数=$c"
done < /proc/$PID/maps
echo "扫描结束"
