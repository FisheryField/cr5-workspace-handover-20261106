echo "=== properties 目录 ==="
ls -la /dobot/userdata/project/properties/
echo
echo "=== axis.json ==="
cat /dobot/userdata/project/properties/axis.json
echo
echo "=== structure.json ==="
cat /dobot/userdata/project/properties/structure.json
echo
echo "=== ratio_default.json ==="
cat /dobot/userdata/project/properties/ratio_default.json
echo
echo "=== properties/default.json ==="
cat /dobot/userdata/project/properties/default.json
echo
echo "=== settings/default.json ==="
cat /dobot/userdata/project/settings/default.json
echo
echo "=== settings/common.json ==="
cat /dobot/userdata/project/settings/common.json
echo
echo "=== 全盘搜 8.23 / 12.52 之类的偏移常量 ==="
grep -rl "8.23" /dobot/userdata/project/properties /dobot/userdata/project/settings 2>/dev/null | head
echo "=== datasvr/config.json ==="
cat /dobot/userdata/project/settings/datasvr/config.json