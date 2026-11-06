L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== C calibrate window"
grep -an "calibrate/home\|isRequestCalihome\|HomeNumdone\|calihome\|updateEncoderData#489" $L | tail -25
echo "=== C DONE"