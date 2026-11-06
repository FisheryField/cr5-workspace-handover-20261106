#!/bin/sh
# 找健康 boot 做全对比 + 挖 boot 自检脚本
D=/dobot/userdata/CR5_sys_files/project/logs/all

echo '=== 0. 时间 ==='
date

echo ''
echo '=== 1. 全部轮转日志清单 ==='
ls -la $D/ | head -25

echo ''
echo '=== 2. 哪个 log.* 含健康会话的 codesys init（Networkadapter opened） ==='
for f in $D/log $D/log.1 $D/log.2 $D/log.3 $D/log.4 $D/log.5 $D/log.6 $D/log.7 $D/log.8 $D/log.9 $D/log.10 $D/log.11 $D/log.12 $D/log.13 $D/log.14; do
  [ -f "$f" ] || continue
  hit=$(grep -ac 'Networkadapter opened' "$f" 2>/dev/null)
  last=$(grep -a 'robot enabled ,begin' "$f" 2>/dev/null | tail -1 | cut -c1-30)
  echo "$f  init=$hit  lastEnable=$last"
done

echo ''
echo '=== 3. 最近改动的文件精确 mtime ==='
ls -la --full-time /dobot/userdata/CR5_sys_files/project/properties/controlCabType.json /dobot/userdata/SlaveLog 2>/dev/null
cat /dobot/userdata/CR5_sys_files/project/properties/controlCabType.json

echo ''
echo '=== 4. 找写 SlaveLog / codesys check 的脚本 ==='
grep -rl 'codesys check success' /dobot --include='*.sh' 2>/dev/null | head -5
grep -rl 'SlaveLog' /dobot/userdata/*.sh /dobot/*.sh /dobot/root 2>/dev/null | head -5

echo ''
echo '=== 5. logs/codesys 与 logs/gcontrol 目录内容（boot 时刻产物） ==='
ls -la /dobot/userdata/CR5_sys_files/project/logs/codesys/ 2>/dev/null | head -12
ls -la /dobot/userdata/CR5_sys_files/project/logs/gcontrol/ 2>/dev/null | head -12
