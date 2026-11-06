echo "=== /etc/version.conf ==="; cat /etc/version.conf 2>/dev/null; echo
echo "=== /dobot/bin/etc/version.conf ==="; cat /dobot/bin/etc/version.conf 2>/dev/null; echo
echo "=== files containing 3.5.4 ==="; find /dobot/userdata /home/ftp /etc /dobot/bin/etc /opt -type f -size -1M 2>/dev/null | xargs grep -l "3\.5\.4" 2>/dev/null | head -10
echo "=== gcontrol version strings ==="; strings /dobot/bin/gcontrol 2>/dev/null | grep -E "^[0-9]+\.[0-9]+\.[0-9]+" | head -10
echo "=== userdata version-ish files ==="; find /dobot/userdata -maxdepth 2 -type f \( -iname "*version*" -o -iname "*.ver" \) 2>/dev/null | head
echo "=== properties ==="; ls -la /dobot/userdata/project/properties/ 2>/dev/null
echo "=== controllerType/version json ==="; cat /dobot/userdata/project/properties/controllerType.json 2>/dev/null; echo
echo "=== codesys.json path ==="; head -c 200 /dobot/userdata/codesys/codesys.json 2>/dev/null