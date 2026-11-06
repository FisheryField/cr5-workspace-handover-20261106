echo "=== homeEncoder.json 最后一条记录（最近一次标定）==="
awk '/"time"/{t=$0} {buf[NR]=$0} END{}' /dobot/userdata/project/settings/function/homeEncoder.json >/dev/null 2>&1
# 直接取文件末尾 40 行
tail -40 /dobot/userdata/project/settings/function/homeEncoder.json
echo
echo "=== 当前关节值 ==="
wget -q -O - http://127.0.0.1:22000/protocol/exchange 2>/dev/null > /tmp/ex.json
# 用 grep -A 抓 jointCoordinate 数组
grep -a -A 8 '"jointCoordinate"' /tmp/ex.json
echo
echo "=== 当前 Cartesian ==="
grep -a -A 8 '"cartesianCoordinate"' /tmp/ex.json
