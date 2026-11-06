L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== A. any servo error AFTER the flash (14:55 today)? ==="
grep -a "logServoError" $L | tail -20
echo ""
echo "--- count of servo error lines dated 2026-09-24 ---"
grep -a "2026-09-24.*logServoError" $L | wc -l
echo ""
echo "--- all 2026-09-24 lines mentioning error/warn/fail ---"
grep -a "2026-09-24" $L | grep -aiE "error|warn|fail" | tail -20
echo ""
echo "=== B. last 25 lines of the main log ==="
tail -25 $L
echo ""
echo "=== C. processes now ==="
ps | grep -vE "\[|grep" | tail -25
echo "=== DONE ==="
