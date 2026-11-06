echo "=== A homeEncoder"; cat /dobot/userdata/project/settings/function/homeEncoder.json 2>/dev/null; echo
echo "=== B recipe"; ls -la /home/ftp/PlcLogic/Recipe/ 2>/dev/null
echo "=== C SavePos hex"; od -An -tx1 /home/ftp/PlcLogic/Recipe/SavePos.txt 2>/dev/null
echo "=== C2 Update"; cat /home/ftp/PlcLogic/Recipe/Update.txt 2>/dev/null; echo
echo "=== C3 Axes"; cat /home/ftp/PlcLogic/Recipe/SaveAxesValue.AxesValues.txtrecipe 2>/dev/null
echo "=== D logs"; ls /dobot/userdata/CR5_sys_files/project/logs/ 2>/dev/null
echo "=== E alarmfiles"; find /dobot/userdata -maxdepth 3 -iname "*alarm*" 2>/dev/null | head -20
echo "=== F alarmtext"; grep -rls "位置偏差" /dobot/userdata/CR5_sys_files/project/ 2>/dev/null | head -10
echo "=== G version"; grep -a settVersion /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -4
echo "=== DONE"