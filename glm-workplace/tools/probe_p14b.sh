#!/bin/sh
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo "=== 17:59:50-18:00:15 recv/ret/error 全量 ==="
grep -a -h -E '\[2026-10-15 (17:59|18:00):[0-5][0-9]\.[0-9]+\]' "$D"/log* 2>/dev/null | grep -a -E 'recv =|return = -|func = jointmovj|\[error\]' | grep -a -v -E 'virtualWall|CaptureStatus|TryLock|Acquire|FollowError' | sort | tail -30
echo "=== done ==="
