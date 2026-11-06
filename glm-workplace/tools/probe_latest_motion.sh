#!/bin/sh
D=/dobot/userdata/CR5_sys_files/project/logs/all
echo "=== 最近 MovL 收令（位姿参数） ==="
grep -a 'recv = MovL' "$D/log" "$D/log.1" "$D/log.2" "$D/log.3" 2>/dev/null | tail -8
echo
echo "=== 最近 JointMovJ 收令 ==="
grep -a 'recv = JointMovJ' "$D/log" "$D/log.1" "$D/log.2" "$D/log.3" 2>/dev/null | tail -6
echo
echo "=== 最近 get pose / 当前位姿类 ==="
grep -a -E 'getpose|GetPose|current.*pose|pose =' "$D/log" "$D/log.1" 2>/dev/null | tail -6
echo "=== done ==="
