L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== Z 1501 window"; grep -an "2026-09-24 15:0[0-3]" $L | grep -avi "alarm_io\|RealtimeHeartbeat" | head -40
echo "=== Z calihome all"; grep -an "calihome\|cali home\|caliHome" $L | tail -10
echo "=== Z enabled/disabled"; grep -an "robot enabled\|robot disabled\|enable\|disable" $L | grep -avi "alarm_io\|RealtimeHeartbeat" | tail -25
echo "=== DONE"