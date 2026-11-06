#!/bin/sh
chmod +x /tmp/ab_sample.sh
rm -f /tmp/ab_stop
setsid /tmp/ab_sample.sh < /dev/null > /dev/null 2>&1 &
sleep 6
echo "=== meta ==="; cat /tmp/ab_meta.txt 2>/dev/null
echo "=== raw bytes ==="; wc -c /tmp/ab_raw.bin
echo "=== ts lines ==="; wc -l /tmp/ab_ts.txt
echo "=== 最近 3 个样本（每个 96 字节，取第 1 个 double 的 hex）==="
tail -c 288 /tmp/ab_raw.bin | od -A d -t f8 | head -20
