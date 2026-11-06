#!/bin/sh
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo "=== 目录 ==="
ls -la "$D" 2>/dev/null | tail -25
echo
echo "=== log 尾部原文 ==="
tail -30 "$D/log" 2>/dev/null
echo
echo "=== 各档 MovL/Joint 计数 ==="
for f in "$D"/log "$D"/log.1 "$D"/log.2 "$D"/log.3 "$D"/log.4; do
  [ -f "$f" ] && echo "$f: MovL=$(grep -a -c 'MovL' "$f" 2>/dev/null) JointMovJ=$(grep -a -c 'JointMovJ' "$f" 2>/dev/null)"
done
echo "=== done ==="
