#!/bin/sh
# diag_macro_extract.sh - rescue macro-session evidence from rotated logs before flood overwrites
LOGDIR=/dobot/userdata/CR5_sys_files/project/logs/all
cd $LOGDIR || exit 1

echo "== file time ranges =="
for f in log.1 log.2 log.3 log.4 log.5 log.6; do
  [ -f $f ] && echo "$f: $(head -1 $f | cut -c1-22) .. $(tail -1 $f | cut -c1-22)"
done

echo "== hit counts per file =="
for f in log.1 log.2 log.3 log.4 log.5 log.6; do
  [ -f $f ] && echo "$f: 29999=$(grep -ac 'local port:29999' $f) enable=$(grep -ac 'robot enabled' $f)"
done

echo "== extract events =="
rm -f /tmp/macro_session_extract.txt
for f in log.1 log.2 log.3 log.4 log.5 log.6; do
  [ -f $f ] && grep -a 'local port:29999\|local port:30003\|EnableRobot\|OnMoveJ\|OnMoveL\|OnQueuedCmdStart\|OnQueuedCmdStop\|robot enabled\|robot disabled\|AlarmSysSetBit\|logServoError' $f | sed "s|^|[$f] |" >> /tmp/macro_session_extract.txt
done
wc -l /tmp/macro_session_extract.txt
echo "--- first 40 ---"
head -40 /tmp/macro_session_extract.txt
echo "--- last 30 ---"
tail -30 /tmp/macro_session_extract.txt
echo "== done =="
