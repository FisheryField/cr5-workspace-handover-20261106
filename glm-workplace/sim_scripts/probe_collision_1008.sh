#!/bin/sh
# 只读探针：P5 200mm 直发后冻死事件（10-22 10:08-10:10）控制器侧记录
L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo '=== [1] 10:08:2x-10:09 全部日志行（事件窗） ==='
grep -a '10:08:2\|10:08:3\|10:08:4\|10:08:5\|10:09:' "$L" | tail -80
echo '=== [2] 报警置位最近30条 ==='
grep -a 'AlarmSysSetBit' "$L" | tail -30
echo '=== [3] 伺服错误最近10条 ==='
grep -a 'logServoError' "$L" | tail -10
echo '=== [4] 使能/下使能记录 10:08-10:11 ==='
grep -a 'monitorServoUptime\|robot enabled\|robot disabled' "$L" | tail -20
echo '=== [5] 电源标志最近10条 ==='
grep -a 'uiBodyVolt\|bBodyPowerFlag\|DataAlarmPowerGoodErr' "$L" | tail -10
echo '=== [6] 拖动/示教最近痕迹 ==='
grep -a 'panelJog\|dragMode' "$L" | tail -8
echo '=== [7] 最近 gActualPosition 3条 ==='
grep -a 'PoseTrace: gActualPosition' "$L" | tail -3
