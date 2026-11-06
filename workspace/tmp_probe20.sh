L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== N first appearance of axis-state alarms (0x63/0x66/0x69/0x6c/0x6f/0x72)"
for i in 63 66 69 6c 6f 72 86; do
  echo -n "index=$i first: "
  grep -an "index=0x$i,isOn=1" $L | head -1
done
echo "=== N what happened at 17:13 (kill) / 17:15 (reboot)"
grep -an "2026-09-24 17:1[3-6]" $L | grep -ai "drive\|power\|fault\|error\|state\|enable" | grep -av "alarm_io\|RealtimeHeartbeat\|0000:" | head -25
echo "=== N now"
grep -an "2026-09-24 17:1[7-9]" $L | grep -ai "drive state\|m_DriveState\|powerOn\|PowerOn\|状态" | head -10
echo "=== N DONE"