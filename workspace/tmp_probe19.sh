echo "=== Z api.lua / dobot.lua"
ls -la /dobot/userdata/project/settings/api.lua /dobot/bin/lua/ 2>/dev/null
echo "=== Z grep zero/home/calib in dobot.lua"
grep -ain "zero\|calib\|home" /dobot/bin/lua/dobot.lua 2>/dev/null | head -40
echo "=== Z api.lua grep"
grep -ain "zero\|calib\|home\|Set" /dobot/userdata/project/settings/api.lua 2>/dev/null | head -60
echo "=== Z main control version"
grep -a "Version\|version" /dobot/userdata/CR5_sys_files/project/properties/*.json 2>/dev/null | head -10
cat /dobot/userdata/CR5_sys_files/version 2>/dev/null; cat /dobot/userdata/version 2>/dev/null
ls /dobot/userdata/CR5_sys_files/ 2>/dev/null | head -20
echo "=== Z DONE"