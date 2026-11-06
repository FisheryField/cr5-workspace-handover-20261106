echo "=== homeEncoder.json 现在 ==="
ls -la /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json
cat /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json
echo
echo "=== 谁引用 homeEncoder ==="
strings /dobot/bin/gcontrol 2>/dev/null | grep -i "homeEncoder" | head -10
strings /dobot/bin/lib/libdataSvr.so.1.0.0 2>/dev/null | grep -i "homeEncoder" | head -10
for f in /dobot/bin/gcontrol /dobot/bin/lib/libdataSvr.so.1.0.0 /dobot/bin/lib/libdataSvrPlugin.so.1.0.0; do printf "%-50s " "$f"; strings "$f" 2>/dev/null | grep -c "homeEncoder"; done
echo "=== gcontrol log 里 homeEncoder / home 相关 ==="
grep -a -o -iE ".{0,50}homeEncoder.{0,80}" /dobot/userdata/project/logs/gcontrol/log* 2>/dev/null | head -6
grep -a -o -iE ".{0,40}(jointHomeState|innerEncoder|outEncoder).{0,60}" /dobot/userdata/project/logs/gcontrol/log* /dobot/userdata/project/logs/codesys/log* 2>/dev/null | head -6
echo "=== lua / 脚本里引用 ==="
ls /dobot/bin/lua/ | head -30
grep -rl "homeEncoder" /dobot/bin/lua /dobot/userdata/project/project /dobot/userdata/CR5_sys_files/project 2>/dev/null | head
echo "=== 现在时间 ==="; date