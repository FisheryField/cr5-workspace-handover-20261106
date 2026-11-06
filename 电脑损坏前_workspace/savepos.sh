echo "=== SavePos.txt (100B) ==="; od -A d -t x1 /home/ftp/PlcLogic/Recipe/SavePos.txt 2>/dev/null | head -12
echo "=== SavePos as float32 ==="; od -A d -t f4 /home/ftp/PlcLogic/Recipe/SavePos.txt 2>/dev/null | head -8
echo "=== slaveinfo first 128B ==="; od -A d -t x1 /dobot/userdata/slaveinfo 2>/dev/null | head -10
echo "=== slaveinfo strings ==="; strings /dobot/userdata/slaveinfo 2>/dev/null | head -30
echo "=== port tool strings ==="; strings /dobot/userdata/port 2>/dev/null | head -25
echo "=== tty2ssh strings ==="; strings /dobot/userdata/tty2ssh 2>/dev/null | head -20
echo "=== other model sysfiles zero/calib files ==="; find /dobot/userdata -maxdepth 3 -iname "*zero*" -o -maxdepth 3 -iname "*calib*" 2>/dev/null | head