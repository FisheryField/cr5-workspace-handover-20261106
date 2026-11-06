echo "=== CR5_sys_files ==="; ls -la /dobot/userdata/CR5_sys_files
echo "=== CR5 project ==="; ls -la /dobot/userdata/CR5_sys_files/project | head -30
echo "=== api.ini ==="; cat /dobot/bin/etc/api.ini
echo "=== ioctrl.json ==="; cat /dobot/bin/etc/ioctrl.json
echo "=== modbusctrl.json ==="; cat /dobot/bin/etc/modbusctrl.json
echo "=== smb.conf ==="; cat /dobot/bin/etc/smb.conf
echo "=== codesys.json ==="; cat /dobot/userdata/codesys/codesys.json
echo "=== settings jsons ==="; cat /dobot/userdata/project/settings/default.json; echo "---"; cat /dobot/userdata/project/settings/common.json; echo "---"; cat /dobot/userdata/project/settings/Dobot+.json
echo "=== SlaveLog ==="; head -12 /dobot/userdata/SlaveLog
echo "=== file magic (4 bytes) ==="; head -c 4 /dobot/userdata/port; echo " <-port"; head -c 4 /dobot/userdata/tty2ssh; echo " <-tty2ssh"; head -c 4 /dobot/bin/gcontrol; echo " <-gcontrol"; head -c 4 /dobot/bin/getVersion; echo " <-getVersion"
echo "=== /etc top ==="; ls -la /etc | head -55
echo "=== /etc/mac ==="; cat /etc/mac
echo "=== /etc/CPU_TYPE ==="; cat /etc/CPU_TYPE 2>&1
echo "=== netd ==="; cat /etc/rc.d/init.d/netd 2>/dev/null
echo "=== misc mounts ==="; ls -la /sddisk /udisk 2>/dev/null | head -20