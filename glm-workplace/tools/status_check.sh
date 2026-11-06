#!/bin/sh
# 只读状态确认（对应 HANDOVER.md §3 + §6.3），不做任何改动
echo "===== 1. 主控应用 md5（9a808cd9...=补丁已装 / 8416cf0e...=原版） ====="
md5sum /dobot/userdata/codesys/allST/Application.app
echo
echo "===== 2. 伺服/从站固件版本（settVersion，应含 servo1..6 : 3.1.5.0） ====="
grep -a settVersion /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -14
echo
echo "===== 3. 标零记录（servo calihome done） ====="
grep -a "servo calihome done" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -2
echo
echo "===== 4. 六轴实际位置（gActualPosition，应全 ≈0） ====="
grep -a "PoseTrace: gActualPosition" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -1
echo
echo "===== 5. 使能状态（最近一次 enable/disable） ====="
grep -a "robot enabled\|robot disabled" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -4
echo
echo "===== 6. 最新报警（AlarmSysSetBit 最近 8 条） ====="
grep -a "AlarmSysSetBit" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -8
echo
echo "===== 7. 控制器已运行时长 / 当前时间 ====="
uptime
date
