#!/bin/sh
echo "== md5 of live app =="
md5sum /dobot/userdata/codesys/allST/Application.app 2>/dev/null
md5sum /dobot/userdata/codesys/allST/Application.crc 2>/dev/null
echo "== /tmp/codesysBoot =="
cat /tmp/codesysBoot 2>/dev/null
echo "== codesys log dir (tail) =="
ls -la /dobot/userdata/CR5_sys_files/project/logs/codesys/ 2>/dev/null | tail -8
echo "== all-log dir (tail) =="
ls -la /dobot/userdata/CR5_sys_files/project/logs/all/ 2>/dev/null | tail -8
echo "== 1A00 writes in current codesys log =="
grep -ao 'SDO write ok: Address: [0-9]* Index: 16#1A00 SubIndex: [0-9]* Data: 16#[0-9A-F]*' /dobot/userdata/CR5_sys_files/project/logs/codesys/log 2>/dev/null | tail -40
echo "== readSDO#4624 tail =="
grep -a 'readSDO#4624' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -8
echo "== uptime / procs =="
uptime
ps | grep -v grep | grep -E 'codesys|gcontrol' 
