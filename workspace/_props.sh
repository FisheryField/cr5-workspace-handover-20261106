#!/bin/sh
P=/dobot/userdata/CR5_sys_files/project/properties
echo "=== 目录 ==="
ls -la $P
echo
for f in axis.json structure.json ratio_default.json controllerType.json; do
  echo "=== $f ==="
  cat $P/$f 2>/dev/null | head -60
  echo
done
