echo "=== logs tree ==="
ls -la /dobot/userdata/project/logs
for d in server gcontrol lua algs blackbox all http codesys; do echo "--- $d ---"; ls -la /dobot/userdata/project/logs/$d 2>/dev/null | head -15; done
echo "=== files mentioning zero/offset in userdata (excl logs) ==="
find /dobot/userdata -path "*/logs" -prune -o -name lost+found -prune -o -type f -size -2M -print 2>/dev/null | xargs grep -il "zero\|offset" 2>/dev/null | head -30
echo "=== default.json (first 1800 bytes) ==="
head -c 1800 /dobot/userdata/project/properties/default.json
echo
echo "=== SavePos.txt vs Recipe ==="
ls -la /home/ftp/PlcLogic/Recipe/
echo "=== blackbox contents ==="
find /dobot/userdata/project/logs/blackbox -type f 2>/dev/null | head -10
echo "=== server logs ==="
find /dobot/userdata/project/logs/server -type f 2>/dev/null | head -10
echo "=== gcontrol logs ==="
find /dobot/userdata/project/logs/gcontrol -type f 2>/dev/null | head -10