L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== W modifyServoParams traces"
grep -an "modifyServoParams\|parseAndReqSet\|SDOWRCount\|the key\|servoParams.json" $L | tail -25
echo "=== W http 400"
grep -an "400\|bad request\|Bad Request" $L | tail -10
echo "=== W DONE"