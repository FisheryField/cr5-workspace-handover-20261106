echo "=== S SlaveLog"; cat /dobot/userdata/SlaveLog
echo "=== S version.json"; cat /mToolServer/control/version.json; echo
echo "=== S supportRules"; cat /mToolServer/control/supportRules.json; echo
echo "=== S 450run.sh"; cat /mToolServer/control/450run.sh
echo "=== S 353run.sh"; cat /mToolServer/control/353run.sh
echo "=== S controller version"; find /dobot/userdata/CR5_sys_files/project -maxdepth 2 -name "*.json" | head -20
cat /dobot/userdata/CR5_sys_files/project/properties/version.json 2>/dev/null | head -30
echo "=== S bin version"; ls /dobot/bin/ | head -40
echo "=== DONE"