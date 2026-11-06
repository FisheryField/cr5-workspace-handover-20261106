echo "=== A. /mToolServer dir ==="
ls -la /mToolServer/ 2>/dev/null
echo ""
echo "=== B. control subdir ==="
ls -la /mToolServer/control/ 2>/dev/null
echo ""
echo "=== C. mToolServer.log (tail 80, no grep filtering) ==="
tail -80 /mToolServer/mToolServer.log 2>/dev/null
echo ""
echo "=== D. updateRunResult.log ==="
cat /mToolServer/updateRunResult.log 2>/dev/null | tail -40
echo ""
echo "=== E. controlRunProcess.log ==="
tail -40 /mToolServer/controlRunProcess.log 2>/dev/null
echo ""
echo "=== F. version.json ==="
cat /mToolServer/control/version.json 2>/dev/null
echo ""
echo "=== G. supportRules.json (head) ==="
head -c 2000 /mToolServer/control/supportRules.json 2>/dev/null
echo ""
echo "=== DONE ==="
