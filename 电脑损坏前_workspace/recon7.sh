echo "=== rcS starts: netd/nope ==="; ls -la /etc/rc.d/init.d/; echo "--- nope ---"; cat /etc/rc.d/init.d/nope 2>/dev/null
echo "=== who references helper binaries ==="; grep -rnE "tty2ssh|slaveinfo|getVersion|mToolServer|logServer" /etc /dobot/bin/dobot.sh /dobot/bin/*.sh /home/ftp 2>/dev/null | head -20
echo "=== who references port ==="; grep -rnE "userdata/port|/port " /etc /dobot/bin/dobot.sh 2>/dev/null | head
echo "=== /etc/fstab ==="; cat /etc/fstab
echo "=== /etc/profile ==="; cat /etc/profile
echo "=== /etc/version.conf ==="; cat /etc/version.conf
echo "=== udisk CODESYSControl.cfg head ==="; head -25 /udisk/CODESYSControl.cfg
echo "=== 3S.dat ==="; cat /udisk/3S.dat; echo; echo "--- SysFileMap.cfg ---"; cat /udisk/SysFileMap.cfg
echo "=== ftp PlcLogic/Application ==="; ls -la /home/ftp/PlcLogic/Application | head
echo "=== projectOld ==="; ls -la /dobot/userdata/projectOld | head -15
echo "=== CR5 project/project ==="; ls /dobot/userdata/CR5_sys_files/project/project | head -30
echo "=== test.lua head ==="; head -25 /dobot/userdata/CR5_sys_files/project/test.lua