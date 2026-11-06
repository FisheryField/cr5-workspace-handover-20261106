echo "=== V version files"
cat /dobot/userdata/project/properties/*ersion*.json 2>/dev/null | head -20
grep -a "mainControl" /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -3
echo "=== V mtool log"
ls -la /mToolServer/ 2>/dev/null | head -20
tail -60 /mToolServer/mToolServer.log 2>/dev/null
echo "=== V savepos/recipe mtimes"
ls -la /home/ftp/PlcLogic/Recipe/ /home/ftp/PlcLogic/Application/ 2>/dev/null
echo "=== V first alarm134 context"
grep -an "0000: 86" /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | head -3
grep -an "0000: 86" /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | wc -l
echo "=== V deviat/enable log"
grep -ain "deviat\|calihome\|enabled\|disabled" /dobot/userdata/CR5_sys_files/project/logs/gcontrol/* 2>/dev/null | tail -20
echo "=== DONE"