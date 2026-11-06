ls -la /dobot/userdata/project/logs/codesys/ | head -6
echo ===CURRENT===
tail -30 /dobot/userdata/project/logs/codesys/log 2>/dev/null | tail -20
echo ===CODESYS-PROC===
ps | grep codesys | grep -v grep
cat /proc/14696/status 2>/dev/null | head -4
