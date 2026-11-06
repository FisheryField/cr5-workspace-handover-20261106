echo "=== settings/function 完整列表 ==="
ls -la /dobot/userdata/CR5_sys_files/project/settings/function/
echo "=== 最近 1 小时内修改/新建的文件（排除 logs）==="
find /dobot/userdata /home/ftp /etc /opt -type f -mmin -60 2>/dev/null | grep -v "/logs/" | grep -v lost+found | head -40
echo "=== projectOld 里的 settings/function ==="
ls -la /dobot/userdata/projectOld/settings/function/ 2>/dev/null | head -50
echo "=== 其它机型目录里有没有 homeEncoder.json ==="
find /dobot/userdata -name "homeEncoder.json" 2>/dev/null
echo "=== 现在时间 ==="; date