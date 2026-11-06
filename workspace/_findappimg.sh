PAT="4465766963652e4170706c69636174696f6e2e496f436f6e"
PID=$(pidof codesyscontrol)
echo "codesyscontrol pid=$PID"
echo "=== 在所有可读映射里搜这个 24 字节模式 ==="
while read -r line; do
  set -- $line
  range=$1; perm=$2
  case "$perm" in r*) ;; *) continue;; esac
  start=${range%%-*}; end=${range##*-}
  sz=$(( 0x$end - 0x$start ))
  [ $sz -lt 4096 ] && continue
  [ $sz -gt 67108864 ] && continue
  cnt=$(dd if=/proc/$PID/mem bs=4096 skip=$((0x$start/4096)) count=$((sz/4096)) 2>/dev/null | od -An -tx1 -v | tr -d ' \n' | grep -oc "$PAT")
  [ "$cnt" != "0" ] && echo "  ★ 命中 x$cnt   映射 $range $perm $6"
done < /proc/$PID/maps
echo "扫描结束"
