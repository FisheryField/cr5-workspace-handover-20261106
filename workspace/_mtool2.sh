strings -n 3 /mToolServer/mToolServer 2>/dev/null | grep -aE "^(update|fault|protocol|settings|config|servo|param|sdo|motor|joint|debug|test)[a-zA-Z/_-]*$|^/[a-z]" | sort -u | head -60
echo "=== 含 http/uri/query 的行 ==="
strings -n 6 /mToolServer/mToolServer 2>/dev/null | grep -aiE "Query Param|SDO slave|uri|httpCallback|evhttp|request" | sort -u | head -40
echo "=== 端口/回调 ==="
strings -n 4 /mToolServer/mToolServer 2>/dev/null | grep -aE "22002|22000|:80|listen" | sort -u | head -20
