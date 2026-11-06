#!/bin/sh
# codesys 侧 boot 日志对比：正常 boot vs 病态 boot
C=/dobot/userdata/CR5_sys_files/project/logs/codesys
BB=/dobot/userdata/CR5_sys_files/project/logs/blackbox

echo '=== 0. 时间 ==='
date

echo ''
echo '=== 1. 各 codesys log 的起止时间戳 ==='
for f in $C/log $C/log.1 $C/log.2 $C/log.3 $C/log.4 $C/log.5 $C/log.6 $C/log.7; do
  [ -f "$f" ] || continue
  echo "--- $f"
  grep -a '2026-' "$f" | head -1 | cut -c1-50
  grep -a '2026-' "$f" | tail -1 | cut -c1-50
done

echo ''
echo '=== 2. SDO write 索引直方图：正常 boot（log.4/5/7） ==='
for f in $C/log.4 $C/log.5 $C/log.7; do
  [ -f "$f" ] || continue
  echo "--- $f"
  grep -a 'SDO write ok' "$f" | grep -o 'Index: 16#[0-9A-Fa-f]*' | sort | uniq -c | sort -rn | head -12
done

echo ''
echo '=== 3. SDO write 索引直方图：病态 boot（log.2 = 报警后 / log = 10:40 冷启动后） ==='
for f in $C/log.2 $C/log; do
  [ -f "$f" ] || continue
  echo "--- $f"
  grep -a 'SDO write ok' "$f" | grep -o 'Index: 16#[0-9A-Fa-f]*' | sort | uniq -c | sort -rn | head -12
done

echo ''
echo '=== 4. 病态 boot codesys log 里的错误行 ==='
grep -an 'Error=[1-9]\|error\|fail\|Fail' $C/log.2 | grep -av 'Error=0' | head -15
echo '--- current boot:'
grep -an 'Error=[1-9]\|error\|fail\|Fail' $C/log | grep -av 'Error=0' | head -15

echo ''
echo '=== 5. 正常 boot codesys log 里的错误行（对照） ==='
grep -an 'Error=[1-9]\|error\|fail\|Fail' $C/log.4 $C/log.7 2>/dev/null | grep -av 'Error=0' | head -10

echo ''
echo '=== 6. blackbox 目录 ==='
ls -la $BB/ 2>/dev/null | head -8

echo ''
echo '=== 7. 病态 boot 有而正常 boot 没有的关键词扫描（零点/偏置/变体选择） ==='
for f in $C/log.2 $C/log $C/log.4 $C/log.7; do
  [ -f "$f" ] || continue
  echo "--- $f"
  grep -aic 'zero\|offset\|calib\|homew\|1A00' "$f"
done
