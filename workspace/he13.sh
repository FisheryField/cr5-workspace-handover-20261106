L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== settVersion 完整块 ==="
grep -a -A14 "settVersion#4488" $L | head -20
grep -a -B4 -A16 "servo1  :3.1.5.0" $L | head -30
echo
echo "=== 硬件版本/代次 ==="
grep -a -o -iE ".{0,70}(hardware ?version|hardwareVersion|hwVersion|HW version).{0,70}" $L | sort -u | head -15
echo
echo "=== mToolServer 支持的 update 接口 ==="
strings /mToolServer/mToolServer | grep -a -E "^/update" | sort -u | head -30
echo
echo "=== mToolServer.log: update 请求历史 ==="
grep -a -E "request update type|singleFwAndXml|update/|file name|firmware name|\.bin|\.efw" /mToolServer/mToolServer.log | tail -40