#!/bin/sh
# 只读取证：找"断电不灭"的持久化机制
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== 0. 时间与 uptime ==='
date; cat /proc/uptime

echo ''
echo '=== 1. 最近 200 分钟内被改过的非日志文件（持久化嫌疑） ==='
find /dobot/userdata -type f -mmin -200 2>/dev/null | grep -v '/logs/' | head -30

echo ''
echo '=== 2. codesys 目录与持久化文件状态 ==='
ls -la /dobot/userdata/codesys/ 2>/dev/null
ls -la /dobot/userdata/codesys/allST/ 2>/dev/null | head -20

echo ''
echo '=== 3. 新 boot（393150 行起）事件链（时间戳） ==='
awk 'NR>=393150 && /PowerOn|robot enabled|robot disabled|clearError|AlarmSysSetBit|handleEmergency|gPowerDown|monitorServoUptime/ {print NR": "$0}' $LOG | head -50

echo ''
echo '=== 4. 新 boot 后 gActual 翻原始系的行号与次数 ==='
awk 'NR>=393150 && /gActualPosition:  8\./ {c++; if(c<=4) print NR": "$0} END {print "raw-frame gActual total: "c+0}' $LOG

echo ''
echo '=== 5. 新 boot EtherCAT init 错误/OP 迁移 ==='
awk 'NR>=393400 && NR<=395500 && /IoDrvEtherCAT/ && (/Error=[1-9]/ || /operational/ || /failed/ || /timeout/ || /Synchroni/)' $LOG | head -25

echo ''
echo '=== 6. 本次 boot SDO write 索引统计（对比健康 boot 找缺失步骤） ==='
awk 'NR>=393150 && /SDO write ok/ {if (match($0,/Index: 16#[0-9A-Fa-f]+/)) print substr($0,RSTART,RLENGTH)}' $LOG | sort | uniq -c | sort -rn | head -25

echo ''
echo '=== 7. 日志目录与历史覆盖范围 ==='
ls -la /dobot/userdata/CR5_sys_files/project/logs/all/ 2>/dev/null | head
ls -la /dobot/userdata/CR5_sys_files/project/logs/ 2>/dev/null | head
head -3 $LOG | cut -c1-60
grep -am1 '2026-10-09' $LOG | cut -c1-40
grep -am1 '2026-09-2' $LOG | cut -c1-40

echo ''
echo '=== 8. wget SDO 直读：J1/J5 的 0x6064 与 J1 的 0x607C（home offset） ==='
wget -q -O - --timeout=8 --header='Content-Type: application/json' --post-data='{"body":[{"key":"addr606400","servoNum":"J1"},{"key":"addr606400","servoNum":"J5"},{"key":"addr607c00","servoNum":"J1"}]}' http://127.0.0.1:22000/settings/readServoParams 2>&1
echo ''
sleep 2
grep -a 'readSDO' $LOG | tail -6
