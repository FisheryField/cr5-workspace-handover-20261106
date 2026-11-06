#!/bin/sh
# 带时间戳取 FollowError 前后的日志 + 使能/去使能事件
echo "== FollowError blocks with timestamps =="
tail -c 3000000 /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | strings | grep -aB2 -A2 'Move FollowError: MoveFollowError Calc' | head -60
echo
echo "== enable/disable/stop events (timestamped lines) =="
tail -c 3000000 /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | strings | grep -aE '^\[?[0-9]{4}-[0-9]{2}-[0-9]{2}|robot (en|dis)abled|Stop FollowError|clear.*error|fault|Fault' | tail -40
