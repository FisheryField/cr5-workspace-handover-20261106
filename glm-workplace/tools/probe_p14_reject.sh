#!/bin/sh
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo "=== 17:32:50-17:34:00 全部 recv ==="
grep -a -h -E '\[2026-10-15 17:3[23]:[0-5][0-9]\.[0-9]+\]|\[2026-10-15 17:34:0[0-9]\.[0-9]+\]' "$D"/log* 2>/dev/null | grep -a 'recv =' | sort | tail -30
echo "=== 同窗 return = -/error ==="
grep -a -h -E '\[2026-10-15 17:3[23]:[0-5][0-9]\.[0-9]+\]' "$D"/log* 2>/dev/null | grep -a -E 'return = -|\[error\]' | sort | tail -15
echo "=== done ==="
