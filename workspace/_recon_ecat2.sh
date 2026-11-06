#!/bin/sh
for d in /dobot/userdata/CR5_sys_files/project /dobot/userdata/project; do
  echo "=== $d 结构（3 层）==="
  find "$d" -maxdepth 3 2>/dev/null | head -60
done
echo "=== 全盘找 ENI / EtherCAT 组态 ==="
find / -xdev \( -iname '*.eni' -o -iname '*EtherCAT*' -o -iname '*ecat*' -o -iname '*.esx' -o -iname '*slave*.xml' \) 2>/dev/null | grep -v proc | head -40
echo "=== codesys 目录 ==="
ls -la /dobot/userdata/codesys 2>/dev/null | head -40
echo "=== 找含 1A00 映射的文本 ==="
grep -rl "1A00\|0x1a00" /dobot/userdata 2>/dev/null | head -20
