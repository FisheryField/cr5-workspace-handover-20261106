#!/bin/sh
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo "=== run2 P6 窗口 16:30:31-16:31:15 ==="
grep -a -h -E '\[(2026-10-15 16:30:(3[1-9]|[45][0-9])|2026-10-15 16:31:(0[0-9]|1[0-9]))\.[0-9]+\]' "$D"/log* 2>/dev/null | grep -a -E 'recv =|ret = .*jointmovj|error|Error|return = -' | grep -a -v -E 'FollowError|virtualWall|CaptureStatus|TryLock|Acquire' | sort | tail -50
echo "=== done ==="
