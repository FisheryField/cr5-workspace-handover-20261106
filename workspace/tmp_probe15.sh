L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== L last 60 relevant"
grep -an "settControlMode : \|not collision\|AlarmSysSetBit\|isRequestCalihome\|HomeNumdone\|calihome done\|clearError\|clearAlarm\|robot enabled\|robot disabled\|g_isErr" $L | grep -av "0000: 86" | tail -45
echo "=== L DONE"