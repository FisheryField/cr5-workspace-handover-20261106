echo "=== mToolServer HTTP routes ==="
strings /mToolServer/mToolServer 2>/dev/null | grep -E "^/[a-zA-Z0-9_]+" | sort -u | head -100
echo "=== mToolServer zero/calib/param strings ==="
strings /mToolServer/mToolServer 2>/dev/null | grep -iE "zero|calib|homing|encoder|offset|param|slave" | sort -u | head -60
echo "=== protocolFunc names ==="
strings /mToolServer/mToolServer 2>/dev/null | grep -iE "protocolFunc|httpCallback|updateFunc" | sort -u | head -40