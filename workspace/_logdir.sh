#!/bin/sh
# List log dir (find rotated logs) before running my experiment
echo "=== logs dir ==="
ls -la /dobot/userdata/CR5_sys_files/project/logs/all/
echo "=== logs parent ==="
ls -la /dobot/userdata/CR5_sys_files/project/logs/
echo "=== log head time ==="
head -c 2000 /dobot/userdata/CR5_sys_files/project/logs/all/log | grep -ao '2026-[0-9/: -]*' | head -3
echo "=== first/last timestamps ==="
grep -ao '2026-09-24 [0-9:]*' /dobot/userdata/CR5_sys_files/project/logs/all/log | head -1
grep -ao '2026-09-24 [0-9:]*' /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -1
