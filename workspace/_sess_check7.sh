#!/bin/sh
echo "== per-slave 1A00 entries this boot (grep -o extracted) =="
for a in 1003 1004 1005 1006 1007 1008; do
  echo "--- slave $a ---"
  grep -ao "Address: $a Index: 16#1A00 SubIndex: [0-9]* Data: 16#[0-9A-F]*" /dobot/userdata/CR5_sys_files/project/logs/codesys/log 2>/dev/null | tail -5
done
