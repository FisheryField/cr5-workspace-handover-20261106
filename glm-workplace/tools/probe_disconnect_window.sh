#!/bin/sh
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo "=== 16:22:44-16:23:31 recv/ret/错误 ==="
grep -a -h -E '\[(2026-10-15 16:22:(4[4-9]|5[0-9])|2026-10-15 16:23:([0-2][0-9]|3[01]))\.[0-9]+\]' "$D"/log* 2>/dev/null | grep -a -E 'recv =|ret =|error|Error|return = -' | grep -a -v -E 'FollowError|virtualWall|CaptureStatus|TryLock|AcquireBlock' | sort | tail -40
echo "=== done ==="
