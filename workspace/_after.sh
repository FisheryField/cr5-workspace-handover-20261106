chmod +x /tmp/zeroprobe.sh
rm -rf /tmp/zp_20260923_113642_after
/tmp/zeroprobe.sh zp_20260923_113642_after 2>&1 | tail -4
echo '--- state.txt 关键行 ---'
grep -E "base_hex|pid=|10MB segment" /tmp/zp_20260923_113642_after/state.txt
