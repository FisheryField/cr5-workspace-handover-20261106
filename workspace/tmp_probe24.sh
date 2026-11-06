L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== S what happened in the last minutes"
grep -an "2026-09-24 17:2[5-9]\|2026-09-24 17:3[0-9]" $L | grep -ai "settControlMode\|robot enabled\|robot disabled\|AlarmSysSetBit\|enableRobot#40\|CheckEnableDirection\|Error\|Drive=" | grep -av "alarm_io\|RealtimeHeartbeat" | head -40
echo "=== S Update.txt"
cat /home/ftp/PlcLogic/Recipe/Update.txt
echo "=== S procs"
ps | grep -E "codesys|gcontrol" | grep -v grep
echo "=== S DONE"