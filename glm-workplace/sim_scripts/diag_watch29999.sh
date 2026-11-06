#!/bin/sh
# diag_watch29999.sh - 30s window: what the RoboDK macro connection actually sends
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "== connect/disconnect + dispenser activity, live 30s =="
BEFORE=$(wc -l < "$LOG")
sleep 30
AFTER=$(wc -l < "$LOG")
echo "log lines: $BEFORE -> $AFTER"
sed -n "$((BEFORE+1)),${AFTER}p" "$LOG" | grep -a '29999\|30003\|tcpDispenser\|accepted\|OnMove\|QueuedCmd\|EnableRobot\|Sync' | head -30
echo "== done =="
