#!/bin/sh
# 决定性对比：homeEncoder.json 当前版 vs 备份版
F=/dobot/userdata/CR5_sys_files/project/settings/function

echo '=== 0. 时间 ==='
date

echo ''
echo '=== 1. homeEncoder.json（当前生效） ==='
ls -la --full-time $F/homeEncoder.json $F/homeEncoder.json.bak_184604
echo '--- 内容:'
cat $F/homeEncoder.json
echo ''
echo '--- 备份内容:'
cat $F/homeEncoder.json.bak_184604
echo ''

echo ''
echo '=== 2. servoParams.json（0x86/偏差阈值等） ==='
cat $F/servoParams.json

echo ''
echo '=== 3. settings 下其他 184604/0927 时段备份 ==='
find /dobot/userdata/CR5_sys_files/project -name '*.bak*' -o -name '*.backup' 2>/dev/null | head -15

echo ''
echo '=== 4. jointMaxParas / default.json 里有无零点相关键 ==='
grep -o '"[a-zA-Z]*[Zz]ero[a-zA-Z]*"\|"[a-zA-Z]*[Hh]ome[a-zA-Z]*"\|"[a-zA-Z]*[Oo]ffset[a-zA-Z]*"' /dobot/userdata/CR5_sys_files/project/settings/function/jointMaxParas.json /dobot/userdata/CR5_sys_files/project/settings/default.json 2>/dev/null | sort -u | head -15
