#!/bin/sh
# 只读取证：驱动器本体 0x6064/0x6062 实测 + EtherCAT OP 状态 + 补丁在位确认
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== 1. 当前最后 2 条 gActualPosition（掉使能态读数） ==='
grep -a 'PoseTrace: gActualPosition' $LOG | tail -2 | sed 's/\[INFO\].*PoseTrace: //'

echo ''
echo '=== 2. 心跳重启边界（algs 何时重启的） ==='
grep -an 'RealtimeHeartbeat' $LOG | awk -F: '{print $1}' | awk 'NR==1{prev=$1;next}{if($1-prev>100){print "gap at line "$1" (prev "prev")"};prev=$1}' | tail -3

echo ''
echo '=== 3. EtherCAT 从站状态相关（OP/SAFEOP） ==='
grep -an 'AlState\|al_state\|to OP\|SAFEOP\|Safeop\|request.*state\|60948\|60949' $LOG | tail -8

echo ''
echo '=== 4. PDO 补丁映射（0x1A00 末条，启动时打的日志） ==='
grep -an '60640020\|60620020\|last=' $LOG | tail -6

echo ''
echo '=== 5. 主控 app 指纹（应仍为补丁版 9a808cd9） ==='
md5sum /dobot/userdata/codesys/allST/Application.app

echo ''
echo '=== 6. HTTP SDO 直读驱动器：J1/J2 的 0x6064 与 0x6062 ==='
B='{"body":[{"key":"addr606400","servoNum":"J1"},{"key":"addr606200","servoNum":"J1"},{"key":"addr606400","servoNum":"J2"},{"key":"addr606200","servoNum":"J2"}]}'
if command -v curl >/dev/null 2>&1; then
  curl -s -m 8 -X POST -H 'Content-Type: application/json' -d "$B" http://127.0.0.1:22000/settings/readServoParams
  echo ''
else
  echo '(no curl on device)'
fi

echo ''
echo '=== 7. SDO 读到的真值（日志 readSDO 行） ==='
grep -an 'readSDO' $LOG | tail -8
