echo "=== region inventory (readable maps) ==="
awk '$2 ~ /^r/ {print $1}' /proc/376/maps | while read r; do
  s=${r%-*}; e=${r#*-}
  printf "0x%s 0x%x\n" "$s" $((0x$e - 0x$s))
done > /tmp/regions.txt
wc -l /tmp/regions.txt
echo "--- writable+exec or anonymous regions ---"
awk '{print}' /tmp/regions.txt | head -60
echo
echo "=== dump merged high range 0x73000000 + 0x4000000 (64 MiB) ==="
/tmp/amrd 376 73000000 4000000 raw | gzip -1 > /tmp/high.bin.gz
ls -l /tmp/high.bin.gz
echo "=== dump merged low range 0x00008000 + 0x800000 (8 MiB) ==="
/tmp/amrd 376 8000 800000 raw | gzip -1 > /tmp/low.bin.gz
ls -l /tmp/low.bin.gz
echo "=== free ==="
df -h /tmp | tail -1
echo "=== END ==="
