L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== A. uptime (did the cabinet get power-cycled?) ==="
cat /proc/uptime
echo "date now: $(date)"
echo ""
echo "=== B. last settVersion block ==="
grep -a -n "settVersion" $L | tail -14
echo ""
echo "=== C. calibrate / calihome events (last 20) ==="
grep -a -n "calihome\|cali home\|calibrate\|Calibrate" $L | tail -20
echo ""
echo "=== D. homeEncoder.json LAST entry only ==="
tail -30 /dobot/userdata/project/settings/function/homeEncoder.json
echo ""
echo "=== E. all 2026-09-24 errors ==="
grep -a "2026-09-24" $L | grep -aiE "error|fail" | tail -12
echo ""
echo "=== F. servo related today ==="
grep -a "2026-09-24" $L | grep -ai "servo" | tail -15
echo "=== DONE ==="
