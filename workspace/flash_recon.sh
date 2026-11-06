echo "=== A. full settVersion block ==="
grep -a -n "settVersion" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -25
echo ""
echo "=== B. historic FoE write lines ==="
grep -a -n "FoE write" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -10
echo ""
echo "=== C. upgrade endpoint mentions in log ==="
grep -a -n "singleFw\|mToolServer\|ToolServer" /dobot/userdata/CR5_sys_files/project/logs/all/log | tail -10
echo ""
echo "=== D. /dobot/bin listing ==="
ls -la /dobot/bin/
echo ""
echo "=== E. CR5_sys_files listing ==="
ls -la /dobot/userdata/CR5_sys_files/
echo "=== DONE ==="
