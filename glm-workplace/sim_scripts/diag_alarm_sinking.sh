#!/bin/sh
# 只读取证：主控版本 / 当前报警 / 使能-下坠时间线 / 零点状态
# 全部为 grep/cat/md5sum/ls，不写任何东西

echo '=== 1. Application.app md5 (主控版本指纹) ==='
md5sum /dobot/userdata/codesys/allST/Application.app 2>/dev/null
ls -la /dobot/userdata/codesys/allST/ 2>/dev/null | head -5

echo ''
echo '=== 2. 当前报警/故障状态 ==='
grep -a 'AlarmSysSetBit\|AlarmSysReset\|logServoError' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -15

echo ''
echo '=== 3. 最近 3 次使能/下使能时间线 ==='
grep -a 'robot enabled\|robot disabled\|this enable last' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -12

echo ''
echo '=== 3b. 最近一次急停/清故障/碰撞相关 ==='
grep -a 'emerg\|Est op\|collision\|Collision\|ClearError\|clear error' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -10

echo ''
echo '=== 4. 零点状态：最后一次标零 ==='
grep -a 'HomeNumdone\|servo calihome' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -6

echo ''
echo '=== 5. 当前六轴实际位置（PoseTrace 最后一行） ==='
grep -a 'PoseTrace: gActualPosition' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -3

echo ''
echo '=== 6. 主控版本行 ==='
grep -a 'settVersion\|controllerVersion\|version' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -5

echo ''
echo '=== 7. 启动时刻+PID ==='
ps | grep -v grep | grep -i 'codesys\|gcontrol' | head -5
