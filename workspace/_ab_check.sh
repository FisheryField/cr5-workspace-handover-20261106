#!/bin/sh
cat /tmp/ab_meta.txt
echo "raw=$(wc -c < /tmp/ab_raw.bin)  ts=$(wc -l < /tmp/ab_ts.txt)"
echo "--- 进程 ---"
ps | grep ab_sample | grep -v grep
echo "--- 采样速率 ---"
echo "now uptime: $(cat /proc/uptime)"
