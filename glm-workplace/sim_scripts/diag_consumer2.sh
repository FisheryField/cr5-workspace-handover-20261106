#!/bin/sh
# 收尾：/dobot 全部可执行与库扫 homeEncoder + 精确 mtime
echo '=== 0. 时间 ==='
date

echo ''
echo '=== 1. homeEncoder.json 精确时间戳（busybox ls -e） ==='
ls -le /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json.bak_184604

echo ''
echo '=== 2. /dobot/bin 全部二进制扫 homeEncoder ==='
for f in /dobot/bin/bin/* /dobot/bin/*; do
  [ -f "$f" ] || continue
  n=$(grep -ac 'homeEncoder' "$f" 2>/dev/null)
  [ "$n" != "0" ] && echo "$f : hits=$n"
done
echo '(scan done)'

echo ''
echo '=== 3. /dobot/lib 与 /usr/lib 重点库扫 ==='
for f in /dobot/lib/*.so* /dobot/bin/lib/*.so*; do
  [ -f "$f" ] || continue
  n=$(grep -ac 'homeEncoder' "$f" 2>/dev/null)
  [ "$n" != "0" ] && echo "$f : hits=$n"
done
echo '(scan done)'

echo ''
echo '=== 4. /dobot/bin 文件清单（找标定类工具） ==='
ls /dobot/bin/ | head -40

echo ''
echo '=== 5. 当前 homeEncoder.json 的字节数与最后一条记录时间 ==='
wc -c /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json
