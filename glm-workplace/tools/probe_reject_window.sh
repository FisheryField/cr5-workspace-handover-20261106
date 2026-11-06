#!/bin/sh
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo "=== 15:54:34-15:55:00（全部轮转档） ==="
grep -a -h -E '\[2026-10-15 15:54:(3[4-9]|[45][0-9])\.[0-9]+\]|\[2026-10-15 15:55:0[0-9]\.[0-9]+\]' "$D"/log* 2>/dev/null | grep -a -v -E 'FollowError|gActual|nextPose|DemandPose|Position demand|Threshold' | sort | tail -50
echo "=== done ==="
