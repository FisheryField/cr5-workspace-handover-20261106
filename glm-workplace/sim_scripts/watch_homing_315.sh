#!/bin/sh
# watch_homing_315.sh - device-side filtered log follower for the homing attempt
# Prints only homing-relevant lines + heartbeat every 20s. Run via rssh -f.
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
LAST=$(wc -l < "$LOG")
echo "watch start from line $LAST at $(date)"
while true; do
  CUR=$(wc -l < "$LOG")
  if [ "$CUR" -gt "$LAST" ]; then
    sed -n "$((LAST+1)),${CUR}p" "$LOG" | grep -a 'HomeNumdone\|calihome\|homeEncoder\|/calibrate\|robot enabled\|robot disabled\|AlarmSysSetBit\|logServoError\|OnCALIBRATE\|setZero'
    LAST=$CUR
  fi
  echo "HB $(date +%H:%M:%S) line=$LAST"
  sleep 20
done
