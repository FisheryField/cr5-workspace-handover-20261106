L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== Z calihome (recent) ==="
grep -an "calibrate/home\|isRequestCalihome\|HomeNumdone\|calihome done\|calihome not done" $L | tail -12
echo "=== Z 0x86 since the last boot ==="
grep -an "AlarmSysSetBit()#40[67]] index=0x86" $L | tail -4
echo "=== Z homeEncoder newest entry ==="
tail -c 700 /dobot/userdata/project/settings/function/homeEncoder.json
echo
echo "=== Z DONE ==="