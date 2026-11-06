#!/bin/sh
# Filter FollowError spam out of recent logs; show real events in user's run window (19:00-20:05)
cd /dobot/userdata/CR5_sys_files/project/logs/all
echo "=== current log (no FollowError) ==="
grep -av 'FollowError' log | grep -av 'gActualPosition' | tail -80
echo "=== log.1 (no FollowError) ==="
grep -av 'FollowError' log.1 | grep -av 'gActualPosition' | tail -60
echo "=== log.2 (no FollowError) ==="
grep -av 'FollowError' log.2 | grep -av 'gActualPosition' | tail -60
echo "=== log.3 (no FollowError) ==="
grep -av 'FollowError' log.3 | grep -av 'gActualPosition' | tail -40
