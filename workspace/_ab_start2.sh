#!/bin/sh
chmod +x /tmp/ab_sample.sh
rm -f /tmp/ab_stop
setsid /tmp/ab_sample.sh < /dev/null > /dev/null 2>&1 &
sleep 8
cat /tmp/ab_meta.txt
echo "raw=$(wc -c < /tmp/ab_raw.bin)  ts=$(wc -l < /tmp/ab_ts.txt)"
echo "=== 最近 2 个样本 ==="
tail -c 192 /tmp/ab_raw.bin | od -A d -t f8
