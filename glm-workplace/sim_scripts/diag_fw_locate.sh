#!/bin/sh
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo "=== 1. flash/upgrade/burn events 14:00-14:25 in all/log ==="
grep -nE "flash|Flash|upgrade|Upgrade|burn|Burn|update.*firmware|firmware" $LOG | awk -F: '$1>401000' | head -40

echo ""
echo "=== 2. settVersion context around 14:15-14:22 (what triggered reads) ==="
awk 'NR>402600 && NR<405230 && (/settVersion/ || /flash/i || /updat/i)' $LOG | head -20

echo ""
echo "=== 3. firmware-ish files on controller ==="
find /dobot /udisk /tmp /root -name "*.bin" 2>/dev/null | head -20
find /dobot /udisk /tmp -name "*irmware*" -o -name "*DS121*" -o -name "*.fw" 2>/dev/null | head -20

echo ""
echo "=== 4. top-level dirs ==="
ls /dobot/ 2>/dev/null
ls /udisk/ 2>/dev/null
ls /tmp/ 2>/dev/null | head -20

echo ""
echo "=== 5. upgrade/download dirs if any ==="
ls -le /dobot/userdata/upgrade 2>/dev/null | head
ls -le /dobot/upgrade 2>/dev/null | head
