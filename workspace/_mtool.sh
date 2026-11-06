ls -la /mToolServer/ 2>/dev/null | head -20
echo "--- 二进制大小 ---"
ls -la /mToolServer/mToolServer
echo "--- 路由字符串 ---"
strings -n 4 /mToolServer/mToolServer 2>/dev/null | grep -aE "^/[a-zA-Z]" | sort -u | head -80
echo "--- sdo 相关 ---"
strings -n 4 /mToolServer/mToolServer 2>/dev/null | grep -aiE "sdo|servo|param" | sort -u | head -60
