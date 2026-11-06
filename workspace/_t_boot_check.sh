#!/bin/sh
echo ===PS===
ps | grep -E 'codesyscontrol|gcontrol|codesysload' | grep -v grep
echo ===PORTS===
netstat -lnt 2>/dev/null | grep -E '22000|29999|30005'
echo ===MD5===
md5sum /dobot/userdata/codesys/allST/Application.app
echo ===ALARM_LOG===
grep -a 'logServoError\|robot enabled\|robot disabled' /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -8
echo ===CODESYS_LOG_TAIL===
ls -l /dobot/userdata/project/logs/codesys/log
grep -a -o 'All slaves operational\|InitSlaves successfull\|FBError Drive=[0-9]*' /dobot/userdata/project/logs/codesys/log | tail -6
