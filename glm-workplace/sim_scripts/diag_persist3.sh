#!/bin/sh
# 决定性对比：健康 boot vs 病态 boot 的 SDO 下装清单
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
LOG1=/dobot/userdata/CR5_sys_files/project/logs/all/log.1

echo '=== 0. 时间 ==='
date

echo ''
echo '=== 1. SlaveLog（驱动侧日志，尾部 30 行） ==='
tail -30 /dobot/userdata/SlaveLog 2>/dev/null | cut -c1-200

echo ''
echo '=== 2. 全盘找 09:00 后改过的非日志文件（含 userdata 外） ==='
find /dobot -mmin -140 -type f 2>/dev/null | grep -v '/logs/' | grep -v SlaveLog | head -40

echo ''
echo '=== 3. 病态 boot（当前 log）最后一次 All slaves operational 位置 ==='
sick=$(grep -an 'All slaves operational' $LOG | tail -1 | cut -d: -f1)
echo "line $sick"
echo '--- 该窗口内 SDO write 索引清单（去重计数）:'
awk -v s=$((sick-3000)) -v e=$((sick+800)) 'NR>=s&&NR<=e&&/SDO write ok/ {if(match($0,/Index: 16#[0-9A-Fa-f]+ [0-9A-Za-z#]*/)) print substr($0,RSTART,RLENGTH)}' $LOG | awk '{print $2,$3}' | sort | uniq -c | sort -rn | head -40
echo '--- 该窗口内 SDO fail/abort:'
awk -v s=$((sick-3000)) -v e=$((sick+800)) 'NR>=s&&NR<=e' $LOG | grep -ai 'sdo.*fail\|sdo.*abort\|Result: 16#[1-9A-F]' | head -10

echo ''
echo '=== 4. 健康 boot（log.1，09:31 前轮转）最后一次 operational 位置 ==='
hea=$(grep -an 'All slaves operational' $LOG1 | tail -1 | cut -d: -f1)
echo "line $hea"
echo '--- 该窗口内 SDO write 索引清单:'
awk -v s=$((hea-3000)) -v e=$((hea+800)) 'NR>=s&&NR<=e&&/SDO write ok/ {if(match($0,/Index: 16#[0-9A-Fa-f]+ [0-9A-Za-z#]*/)) print substr($0,RSTART,RLENGTH)}' $LOG1 | awk '{print $2,$3}' | sort | uniq -c | sort -rn | head -40
echo '--- 该窗口内 SDO fail/abort:'
awk -v s=$((hea-3000)) -v e=$((hea+800)) 'NR>=s&&NR<=e' $LOG1 | grep -ai 'sdo.*fail\|sdo.*abort\|Result: 16#[1-9A-F]' | head -10

echo ''
echo '=== 5. log.1 健康 boot 的时间戳（确认它覆盖 08:5x） ==='
awk -v s=$((hea-3000)) -v e=$hea 'NR>=s&&NR<=e' $LOG1 | grep -a '2026-10-10 0[89]' | head -2
awk -v s=$((hea-3000)) -v e=$hea 'NR>=s&&NR<=e' $LOG1 | grep -a '2026-10-10 0[89]' | tail -2

echo ''
echo '=== 6. 单键 SDO 读 J5 0x6064（实际位置） ==='
wget -q -O - --timeout=8 --header='Content-Type: application/json' --post-data='{"body":[{"key":"addr606400","servoNum":"J5"}]}' http://127.0.0.1:22000/settings/readServoParams 2>&1
echo ''
sleep 2
grep -a 'readSDO' $LOG | tail -3

echo ''
echo '=== 7. 单键 SDO 读 J5 0x607C（home offset） ==='
wget -q -O - --timeout=8 --header='Content-Type: application/json' --post-data='{"body":[{"key":"addr607c00","servoNum":"J5"}]}' http://127.0.0.1:22000/settings/readServoParams 2>&1
echo ''
sleep 2
grep -a 'readSDO' $LOG | tail -3
