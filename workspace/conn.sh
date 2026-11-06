echo "=== established connections ==="; netstat -tn 2>/dev/null | head -30
echo "=== listeners ==="; netstat -tln 2>/dev/null | head -30