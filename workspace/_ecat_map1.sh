#!/bin/sh
L=/dobot/userdata/CR5_sys_files/project/logs/codesys/log
grep -ao "SDO write ok: Address: [0-9]* Index: 16#[0-9A-Fa-f]* SubIndex: [0-9]* Data: 16#[0-9A-Fa-f]*" $L 2>/dev/null > /tmp/sdow.txt
wc -l /tmp/sdow.txt
echo "=== 按从站统计 ==="
for a in 1003 1004 1005 1006 1007 1008; do
  echo "slave $a : $(grep -c "Address: $a " /tmp/sdow.txt) 行"
done
echo "=== 最后一段（最后一轮配置）各站 1600/1A00 条目 ==="
for a in 1003 1004 1005 1006 1007 1008; do
  echo "--- slave $a RxPDO 0x1600 (最后一次) ---"
  grep "Address: $a Index: 16#1600 SubIndex: [1-9]" /tmp/sdow.txt | tail -40 | sed 's/.*SubIndex: /sub /; s/ Result.*//'
done
