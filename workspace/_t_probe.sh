#!/bin/sh
P=$(ps | grep codesyscontrol | grep -v grep | awk '{print $1}')
echo "PID=$P"
cat /proc/$P/wchan; echo
head -5 /proc/$P/status
echo ===THREADS===
for d in /proc/$P/task/*; do
  n=$(basename $d)
  w=$(cat $d/wchan 2>/dev/null)
  s=$(head -1 $d/stat 2>/dev/null | awk '{print $3}')
  echo "$n state=$s wchan=$w"
done
echo ===FDS===
ls -l /proc/$P/fd 2>/dev/null | wc -l
