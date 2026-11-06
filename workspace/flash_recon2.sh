echo "=== A. /dobot/bin/bin ==="
ls -la /dobot/bin/bin/
echo ""
echo "=== B. /dobot/bin/tmp ==="
ls -laR /dobot/bin/tmp/ | head -40
echo ""
echo "=== C. grep singleFwAndXml under /dobot (bounded) ==="
grep -rl "singleFwAndXml" /dobot/bin /dobot/userdata 2>/dev/null | head -20
echo "--- done C ---"
echo ""
echo "=== D. /dobot/bin/port content ==="
head -50 /dobot/bin/../userdata/CR5_sys_files/port
echo ""
echo "=== E. dobot.sh (what gets started) ==="
grep -n "ToolServer\|upgrade\|Update\|foe\|FoE\|8080\|http" /dobot/bin/dobot.sh
echo ""
echo "=== F. top-level /dobot ==="
ls -la /dobot/
echo "=== DONE ==="
