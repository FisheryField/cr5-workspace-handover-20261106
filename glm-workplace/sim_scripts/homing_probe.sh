#!/bin/sh
# homing_probe.sh - one-shot incremental probe of homing-relevant log lines.
# Keeps its own cursor in /tmp/homing_probe_state (tmp only; log untouched).
# First run backfills the last 3000 lines, then only new lines each call.
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
ST=/tmp/homing_probe_state
CUR=$(wc -l < "$LOG")
LAST=-1
[ -f "$ST" ] && LAST=$(cat "$ST" 2>/dev/null)
if [ "$LAST" -lt 0 ]; then
  LAST=$((CUR - 3000)); [ "$LAST" -lt 0 ] && LAST=0
fi
if [ "$CUR" -gt "$LAST" ]; then
  sed -n "$((LAST+1)),${CUR}p" "$LOG" | grep -a 'HomeNumdone\|calihome\|homeEncoder\|/calibrate\|robot enabled\|robot disabled\|AlarmSysSetBit\|logServoError\|OnCALIBRATE\|setZero\|writeJsonFile.*homeEncoder'
  echo "$CUR" > "$ST"
fi
