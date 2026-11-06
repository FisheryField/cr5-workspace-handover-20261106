#!/bin/sh
# 只读：轮转日志找 settVersion + 确认控制器侧备份完好
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo "===== 各轮转日志里的 settVersion（最近一次） ====="
for f in $D/log $D/log.1 $D/log.2 $D/log.3 $D/log.4; do
  [ -f "$f" ] || continue
  n=$(grep -ac "settVersion" "$f" 2>/dev/null)
  echo "--- $f : $n 行"
  [ "$n" != "0" ] && grep -a "settVersion" "$f" | tail -3
done
echo
echo "===== 控制器侧回退备份（BACKUP_ORIGINAL / BACKUP_pdo_*） ====="
ls -la /dobot/userdata/codesys/BACKUP_ORIGINAL/ 2>/dev/null
md5sum /dobot/userdata/codesys/BACKUP_ORIGINAL/Application.app 2>/dev/null
ls -d /dobot/userdata/codesys/BACKUP_pdo_* 2>/dev/null
echo
echo "===== allST 目录现状 ====="
ls -la /dobot/userdata/codesys/allST/ | head -8
