chmod +x /tmp/zeroprobe.sh
sh -n /tmp/zeroprobe.sh && echo SYNTAX_OK
/tmp/zeroprobe.sh proberehearsal 2>&1 | tail -6
echo '--- state.txt 里关键行 ---'
grep -E "base_hex|pid=|homeEncoder|10MB segment" /tmp/proberehearsal/state.txt | head -5
echo '--- 关键页 od 输出 ---'
sed -n '/关键页/,$p' /tmp/proberehearsal/state.txt | head -14
