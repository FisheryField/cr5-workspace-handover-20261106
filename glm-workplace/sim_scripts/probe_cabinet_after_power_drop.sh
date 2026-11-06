#!/bin/sh
# 只读取证：使能后回退+下坠+断电事件
echo '===== A. controller log tail 90 ====='
tail -n 90 /dobot/userdata/CR5_sys_files/project/logs/all/log
echo
echo '===== B. homeEncoder.json ====='
cat /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json
echo
echo '===== C. alarm/enable keyword lines in recent log ====='
tail -n 6000 /dobot/userdata/CR5_sys_files/project/logs/all/log \
  | grep -nE '0x86|0x74|0x92|0x83|0x82|34322|60948|60949|使能|下坠|掉电|断电|servo|enable|alarm|fault|e-stop|estop' \
  | tail -n 160
echo
echo '===== D. file size/mtime ====='
ls -l /dobot/userdata/CR5_sys_files/project/logs/all/log /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json
echo done
