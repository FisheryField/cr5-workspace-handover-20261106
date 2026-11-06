#!/bin/sh
echo "== all/log exists? =="
ls -la /dobot/userdata/CR5_sys_files/project/logs/all/log 2>&1
echo "== any readSDO lines in current log (tail) =="
grep -a 'readSDO' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -10
echo "== any sdo lines (broad, tail) =="
grep -ai 'sdo read\|sdo write\|readSDO\|writeSDO' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -10
echo "== homeEncoder.json =="
cat /dobot/userdata/project/settings/function/homeEncoder.json 2>/dev/null
