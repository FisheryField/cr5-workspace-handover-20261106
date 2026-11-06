echo "=== .ash_history (full) ==="; cat /root/.ash_history
echo "=== who references save.sh (broad) ==="; find /root /usr /var /bin /sbin /etc /home /opt /dobot/bin -type f -size -2M 2>/dev/null | xargs grep -l "save\.sh" 2>/dev/null | head -10
echo "=== default.json calib-ish keys ==="; grep -inE "zero|calib|offset|encode|home|encoder" /dobot/userdata/CR5_sys_files/project/properties/default.json 2>/dev/null | head -40
echo "=== tslib (touchscreen, not robot) ==="; ls -la /bin/ts_calibrate /etc/ts.conf 2>/dev/null
echo "=== settings/function ==="; ls -la /dobot/userdata/project/settings/function 2>/dev/null
echo "=== redis dump dir ==="; ls -la /dobot/userdata/project/redis 2>/dev/null
echo "=== alarm_servo lines 690-830 sample ==="; sed -n "690,700p;780,800p" /dobot/userdata/CR5_sys_files/project/properties/alarm_servo.json 2>/dev/null