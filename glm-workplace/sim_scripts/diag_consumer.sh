#!/bin/sh
# 谁消费 homeEncoder.json：运行进程二进制字符串扫描
echo '=== 0. 时间 ==='
date

echo ''
echo '=== 1. 运行中进程与其二进制路径 ==='
ps | awk 'NR>1 {print $1}' | while read p; do
  exe=$(readlink /proc/$p/exe 2>/dev/null)
  [ -n "$exe" ] && echo "pid $p -> $exe"
done | head -15

echo ''
echo '=== 2. 各二进制里是否引用 homeEncoder ==='
for p in $(ps | awk 'NR>1 {print $1}'); do
  exe=$(readlink /proc/$p/exe 2>/dev/null)
  [ -z "$exe" ] && continue
  case "$exe" in
    *codesys*|*gcontrol*|*algs*|*DataSvr*|*datasvr*|*lua*|*dobot*)
      n=$(grep -ac 'homeEncoder' "$exe" 2>/dev/null)
      echo "$exe : homeEncoder hits=$n"
      ;;
  esac
done

echo ''
echo '=== 3. 全 project 目录二进制粗扫（限关键名） ==='
for f in $(find /dobot/userdata/CR5_sys_files -maxdepth 3 -type f \( -name '*gcontrol*' -o -name '*algs*' -o -name '*DataSvr*' -o -name '*.so' \) 2>/dev/null | head -12); do
  n=$(grep -ac 'homeEncoder' "$f" 2>/dev/null)
  echo "$f : hits=$n"
done

echo ''
echo '=== 4. codesys 应用里引用（.app 二进制） ==='
grep -ac 'homeEncoder' /dobot/userdata/codesys/allST/Application.app 2>/dev/null
grep -ac 'homeEncoder' /dobot/userdata/codesys/BACKUP_ORIGINAL/Application.app 2>/dev/null
