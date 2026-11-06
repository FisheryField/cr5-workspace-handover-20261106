#!/bin/sh
D=/dobot/userdata/CR5_sys_files/project/logs/all
awk '
/\[2026-10-13 11:3[89]:|\[2026-10-13 11:4[012]:/ {on=1}
/\[2026-10-13 11:4[3-9]:|\[2026-10-13 1[2-9]:/ {on=0}
on {
  if (/PoseTrace: DemandPose/) {
    if ($0 != pd) { d++; if (d<=60) print "D| " $0; pd=$0 }
    next
  }
  if (/PoseTrace/ || /FollowError/ || /ActualPose/) { spam++; next }
  if (/\[2026-10-13/) {
    ts++
    if (/MovL/ || /MOVL/ || /recv/ || /Recv/ || /cmd/ || /\[error\]/ || /Alarm/ || /logServoError/ || /Enable/) {
      m++; if (m<=80) print "M| " $0
    } else if (n<150) { n++; print "T| " $0 }
    next
  }
  u++
}
END { print "== stat: demandpose_changes=" d " ts_lines=" n " matched=" m " other_ts=" ts " nonts=" u " spam=" spam }
' "$D/log.16" "$D/log.15" "$D/log.14"
echo "=== done ==="
