L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== last 6 minutes, control/alarm only ==="
grep -an "2026-09-25 17:3[0-9]\|2026-09-25 17:4[0-9]" $L | grep -ai "settControlMode\|robot enabled\|robot disabled\|AlarmSysSetBit\|not collision\|monitorErrorStatus\|g_isErr\|clearAlarms\|Drive=\|powerOn\|state error" | grep -av "alarm_io\|RealtimeHeartbeat" | tail -40
echo "=== DONE ==="