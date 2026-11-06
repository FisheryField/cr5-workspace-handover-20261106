#!/bin/sh
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo '=== SDO results (ver / 0x6064 / 0x6062) ==='
grep -a 'readSDO#4624' $L | tail -n 20
echo
echo '=== search for the alarm text ==='
for D in /dobot/bin /dobot/userdata /home/ftp /usr/lib; do
  grep -ralf /tmp/_needle.txt $D 2>/dev/null | head -n 8
done
echo '=== in the logs? ==='
grep -alf /tmp/_needle.txt  2>/dev/null | head -n 3
grep -a -f /tmp/_needle.txt  2>/dev/null | tail -n 12
echo '=== END ==='
