#!/bin/sh
grep -a 'sdo read' /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -12
echo "=== raw log around latest sdo ==="
grep -an 'sdo read' /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -3 | cut -d: -f1
