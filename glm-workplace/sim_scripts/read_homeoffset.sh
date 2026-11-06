#!/bin/sh
# 驱动器 0x607C home offset 直读（全部六轴，掉使能态）
# 只读：HTTP POST readServoParams + 日志 readSDO 行
L=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== 0. 时间 ==='
date

echo ''
echo '=== 1. 六轴 0x607C（home offset） ==='
for j in J1 J2 J3 J4 J5 J6; do
  wget -q -O - --timeout=8 --header='Content-Type: application/json' \
    --post-data="{\"body\":[{\"key\":\"addr607c00\",\"servoNum\":\"$j\"}]}" \
    http://127.0.0.1:22000/settings/readServoParams >/dev/null 2>&1
  sleep 1
  v=$(grep -a 'readSDO' $L | grep -a "index=24700" | tail -1 | sed 's/.*value=//;s/\..*//')
  echo "$j 0x607C(raw counts) = $v"
done

echo ''
echo '=== 2. 六轴 0x6064（实际位置，掉使能态） ==='
for j in J1 J2 J3 J4 J5 J6; do
  wget -q -O - --timeout=8 --header='Content-Type: application/json' \
    --post-data="{\"body\":[{\"key\":\"addr606400\",\"servoNum\":\"$j\"}]}" \
    http://127.0.0.1:22000/settings/readServoParams >/dev/null 2>&1
  sleep 1
  v=$(grep -a 'readSDO' $档案 2>/dev/null | tail -1)
  v=$(grep -a 'readSDO' $L | grep -a "index=24676" | tail -1 | sed 's/.*value=//;s/\..*//')
  echo "$j 0x6064 = $v"
done
