#!/bin/sh
echo "== mToolServer flash history (today) =="
grep -a '2026-09-24' /mToolServer/mToolServer.log 2>/dev/null | grep -a 'foe write result\|starting update firmware\|start FoE write' 
echo "== boot log around 17:5x (servo version / calihome / enable) =="
grep -a 'settVersion\|servo1\|servoV' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -12
echo "== recent calibrate/enable events =="
grep -a 'calihome\|calibrate\|robot enabled\|robot disabled\|clearMark' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -25
echo "== codesys boot: slave versions if logged =="
grep -a '0x32D8\|0x3150\|3.1.5.0\|3.2.D.8\|version' /dobot/userdata/CR5_sys_files/project/logs/codesys/log 2>/dev/null | tail -10
