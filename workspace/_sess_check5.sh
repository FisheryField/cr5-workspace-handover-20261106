#!/bin/sh
echo "== per-slave last 1A00 entry (this boot) =="
for a in 1003 1004 1005 1006 1007 1008; do
  last=$(grep -a "Address: $a Index: 16#1A00" /dobot/userdata/CR5_sys_files/project/logs/codesys/log 2>/dev/null | tail -60 | grep -o 'SubIndex: [0-9]* Data: 16#[0-9A-F]*' | tail -1)
  n=$(grep -a "Address: $a Index: 16#1A00 SubIndex: 0 " /dobot/userdata/CR5_sys_files/project/logs/codesys/log 2>/dev/null | grep -o 'Data: 16#[0-9A-F]*' | tail -1)
  echo "slave $a: n=$n last=$last"
done
echo "== servo error log today =="
grep -ac 'logServoError' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null
echo "== calihome events today =="
grep -a 'calihome' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -6
echo "== enable/disable today =="
grep -a 'robot enabled\|robot disabled' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -10
