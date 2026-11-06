echo "=== M control dir"; ls -la /mToolServer/control/ 2>/dev/null
echo "=== M tUpdate"; ls -laR /tmp/tUpdate/ 2>/dev/null | head -60
echo "=== M update flag"; cat /home/ftp/PlcLogic/Recipe/Update.txt; echo
echo "=== M root of dobot userdata"; ls -la /dobot/userdata/ | head -30
echo "=== DONE"