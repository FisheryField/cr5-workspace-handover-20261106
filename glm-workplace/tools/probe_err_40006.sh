#!/bin/sh
echo "=== 搜 -40006 释义（properties/settings/docs） ==="
grep -r "40006" /dobot/userdata/project/properties /dobot/userdata/project/settings /dobot/userdata/project/api 2>/dev/null | head -20
grep -r "40006" /dobot/userdata/CR5_sys_files 2>/dev/null | grep -av Binary | head -10
echo "=== 搜错误码表文件 ==="
grep -rl "40001" /dobot/userdata/project/properties 2>/dev/null | head -5
echo "=== done ==="
