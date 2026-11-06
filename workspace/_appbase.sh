PID=376
START=0x27d000
PAGES=142      # 0x8e000/4096
PAT="4465766963652e4170706c69636174696f6e2e496f436f6e"
echo "=== dump 该映射 ($PAGES 页) ==="
dd if=/proc/$PID/mem bs=4096 skip=$((START/4096)) count=$PAGES of=/tmp/appimg.bin 2>/dev/null
ls -la /tmp/appimg.bin
echo
echo "=== 定位模式字节偏移 ==="
IDX=$(od -An -tx1 -v /tmp/appimg.bin | tr -d ' \n' | awk -v p="$PAT" '{ i=index($0,p); print i }')
echo "  十六进制串中的位置 = $IDX"
if [ "$IDX" -gt 0 ]; then
  BOFF=$(( (IDX-1)/2 ))
  LIVE=$(( START + BOFF ))
  BASE=$(( LIVE - 0x0e9f08 ))
  echo "  镜像内偏移 = 0x$(printf %x $BOFF)"
  echo "  运行时地址 = 0x$(printf %x $LIVE)"
  echo "  ==> 推断加载基址 BASE = 0x$(printf %x $BASE)"
  echo "      (检查是否页对齐: BASE % 4096 = $(( BASE % 4096 )))"
  echo
  echo "=== 对比: 镜像前 32 字节 vs 文件前 32 字节 ==="
  echo -n "  镜像: "; dd if=/tmp/appimg.bin bs=1 count=32 2>/dev/null | od -An -tx1 -v | tr -d '\n'; echo
  echo -n "  文件: "; dd if=/dobot/../ftp/PlcLogic/Application/Application.app bs=1 count=32 2>/dev/null | od -An -tx1 -v | tr -d '\n'; echo
fi
