PID=376
BASE=0x759be000
PAT="IoConfig_Globals.a1.config.write"
echo "=== 找具体 4KB 块 ==="
i=0
HIT=-1
while [ $i -lt 578 ]; do
  off=$(( $i * 4096 ))
  c=$(dd if=/proc/$PID/mem bs=4096 skip=$(( (BASE+off)/4096 )) count=1 2>/dev/null | grep -ac "$PAT")
  if [ "$c" != "0" ]; then
    addr=$(( BASE + off ))
    echo "  ★ 块 $i 地址 0x$(printf %x $addr)"
    HIT=$addr
    break
  fi
  i=$((i+1))
done
[ $HIT -lt 0 ] && { echo "未找到"; exit; }
echo
echo "=== 该块内容 (偏移 -0x40 ~ +0x1c0) ==="
dd if=/proc/$PID/mem bs=1 skip=$((HIT-64)) count=560 2>/dev/null | od -Ax -tx1 -v | head -40
echo
echo "=== 该块的 ASCII ==="
dd if=/proc/$PID/mem bs=1 skip=$((HIT-64)) count=560 2>/dev/null | od -Ax -c -v | head -40
