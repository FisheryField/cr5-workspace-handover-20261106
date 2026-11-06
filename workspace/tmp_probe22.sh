echo "=== SP file"
ls -la /dobot/userdata/project/settings/function/servoParams.json 2>/dev/null
head -c 3000 /dobot/userdata/project/settings/function/servoParams.json 2>/dev/null
echo
echo "=== SP keys"
grep -o "addr[0-9A-Fa-f]*" /dobot/userdata/project/settings/function/servoParams.json 2>/dev/null | sort -u | head -40
echo "=== SP DONE"