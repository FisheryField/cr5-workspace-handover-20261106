#!/bin/sh
# 终局取证：晃动帧定位 + 使能窗口全行 + CiA402 状态直读
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== 0. 时间 ==='
date

echo ''
echo '=== 1. 冷启动段（393150+）原始系帧的行号分布 ==='
awk 'NR>=393150 && /PoseTrace: gActualPosition:  8\./ {print NR}' $LOG | awk 'NR==1{first=$1} {last=$1; c++} END{print "first="first" last="last" count="c+0}'

echo ''
echo '=== 2. 10:35-10:46 关键事件（行号+时间） ==='
awk '/2026-10-10 10:3[5-9]|2026-10-10 10:4[0-6]/ && /enabled|PowerOn|Emergency|AlarmSys|operational|SDO|zero|home|calib|SetPos|SavePos/ {print NR": "substr($0,1,140)}' $LOG | head -50

echo ''
echo '=== 3. 第一帧原始系前后各 6 行（晃动起点上下文） ==='
f=$(awk 'NR>=393150 && /PoseTrace: gActualPosition:  8\./ {print NR; exit}' $LOG)
echo "first raw frame at line $f"
awk -v s=$((f-6)) -v e=$((f+6)) 'NR>=s&&NR<=e {print NR": "substr($0,1,150)}' $LOG

echo ''
echo '=== 4. 10:03:44 使能窗口全部行（393720-393850 太早，取使能行±80 行内的非心跳行） ==='
awk 'NR>=388830 && NR<=388960 && !/RealtimeHeartbeat|PoseTrace/ {print NR": "substr($0,1,140)}' $LOG | head -40

echo ''
echo '=== 5. CiA402 直读：J1 状态字 0x6041 + 编码器原始 0x6063 + homing 方式 0x6098 ==='
wget -q -O - --timeout=8 --header='Content-Type: application/json' --post-data='{"body":[{"key":"addr604100","servoNum":"J1"},{"key":"addr606300","servoNum":"J1"},{"key":"addr609800","servoNum":"J1"}]}' http://127.0.0.1:22000/settings/readServoParams 2>&1
echo ''
sleep 2
grep -a 'readSDO' $LOG | tail -8

echo ''
echo '=== 6. 6041/6063/6098 是否可读（对比 6064 的读法） ==='
grep -ac 'index=24641\|index=24675\|index=24728' $LOG
