echo "=== PlcLogic dirs ==="; ls -la /home/ftp/PlcLogic/ac_persistence /home/ftp/PlcLogic/Recipe /home/ftp/PlcLogic/visu 2>/dev/null | head -40
echo "=== process dir ==="; ls -la /dobot/userdata/project/process 2>/dev/null
echo "=== sixForce ==="; ls -la /dobot/userdata/project/process/sixForce 2>/dev/null; echo "--- calibProcess.json ---"; head -c 600 /dobot/userdata/project/process/sixForce/calibProcess.json 2>/dev/null
echo "=== properties identifiers ==="; for f in axis.json controllerType.json controlCabType.json businessType.json; do printf "%s = " "$f"; cat /dobot/userdata/CR5_sys_files/project/properties/$f 2>/dev/null; echo; done
echo "=== structure.json ==="; cat /dobot/userdata/CR5_sys_files/project/properties/structure.json 2>/dev/null
echo "=== gcontrol dual/LRHand strings ==="; strings /dobot/bin/gcontrol 2>/dev/null | grep -iE "dual|LRHand|Calib" | sort -u | head -40
echo "=== UTF8==="
for f in /home/ftp/PlcLogic/Application/Application.app /dobot/bin/gcontrol /home/ftp/.lib/libCmpDobot6Axes.so /dobot/userdata/CR5_sys_files/project/properties/alarm_controller.json /dobot/userdata/CR5_sys_files/project/properties/alarm_servo.json; do echo "### $f"; grep -a -o -e "零点" -e "标定" -e "编码器" -e "零位" -e "校零" -e "原点" "$f" 2>/dev/null | sort | uniq -c | head -12; done
echo "### alarm context"; grep -a -n -e "零点" -e "零位" -e "标定" /dobot/userdata/CR5_sys_files/project/properties/alarm_controller.json 2>/dev/null | head -10
echo "### servo alarm context"; grep -a -n -e "零点" -e "零位" -e "编码器" /dobot/userdata/CR5_sys_files/project/properties/alarm_servo.json 2>/dev/null | head -8
echo "=== ENDUTF8 ==="