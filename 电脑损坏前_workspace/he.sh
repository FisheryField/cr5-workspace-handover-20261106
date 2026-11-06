echo "=== ls ==="
ls -la --time-style=full-iso /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json 2>/dev/null || ls -la /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json
echo "=== 内容 ==="
cat /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json 2>/dev/null
echo
echo "=== settings/function 目录全览 ==="
ls -la --time-style=full-iso /dobot/userdata/CR5_sys_files/project/settings/function/ 2>/dev/null | head -50
echo "=== 全盘搜 homeEncoder ==="
find / -name "homeEncoder.json" 2>/dev/null | head
echo "=== 对照：projectOld 里有没有 ==="
find /dobot/userdata/projectOld -name "homeEncoder.json" 2>/dev/null | head
echo "=== 当前时间 ==="; date