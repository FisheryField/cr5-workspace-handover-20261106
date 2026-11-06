#!/bin/sh
# 只读：抓最近一次使能前后的报警链 + 伺服错误 + homeEncoder 最新条目
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "total lines: $(wc -l < $LOG)"
EN=$(grep -n 'begin to record enable robot time' $LOG | tail -n 1 | cut -d: -f1)
echo "===== last enable begins at line: $EN ====="
sed -n "$((EN-40)),$((EN+500))p" $LOG | grep -vE 'PoseTrace|RealtimeHeartbeat' | head -c 18000
echo
echo '===== last 30 servo error updates ====='
grep -n 'logServoError' $LOG | tail -n 30
echo
echo '===== last 40 AlarmSysSetBit ====='
grep -n 'AlarmSysSetBit' $LOG | tail -n 40
echo
echo '===== homeEncoder tail ====='
tail -c 700 /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json
echo done
