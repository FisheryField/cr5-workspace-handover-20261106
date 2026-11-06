#!/bin/sh
echo "== codesys log file mtimes =="
ls -la /dobot/userdata/CR5_sys_files/project/logs/codesys/log 2>/dev/null
echo "== last 30 full 1A00 lines =="
grep -a '1A00' /dobot/userdata/CR5_sys_files/project/logs/codesys/log 2>/dev/null | tail -30
echo "== count per slave this file =="
for a in 1003 1004 1005 1006 1007 1008; do
  c=$(grep -ac "Address: $a Index: 16#1A00" /dobot/userdata/CR5_sys_files/project/logs/codesys/log 2>/dev/null)
  echo "slave $a : $c lines"
done
