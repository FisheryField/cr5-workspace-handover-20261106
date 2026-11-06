#!/bin/sh
# 方案B：备份 + 恢复 homeEncoder.json（9/27 17:56:18 好零点，单条记录版）
F=/dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json
TS=$(date +%Y%m%d_%H%M%S)

echo '=== 1. 改前校验：坏文件已另存（本地副本 + 柜上时间戳备份） ==='
ls -la $F
cp -p $F ${F}.corrupt_${TS}
ls -la ${F}.corrupt_${TS}
md5sum $F ${F}.corrupt_${TS}

echo ''
echo '=== 2. 写入恢复版 ==='
cat > $F <<'EOF'
{
    "encoder": [
        {
            "innerEncoder": [
                204984.0,
                -988411.0,
                -877546.0,
                695220.0,
                -320522.0,
                608969.0
            ],
            "outEncoder": [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0
            ],
            "jointHomeState": [
                true,
                true,
                true,
                true,
                true,
                true
            ],
            "date": "2026-09-27",
            "time": "17:56:18"
        }
    ]
}
EOF

echo '=== 3. 改后校验 ==='
ls -la $F
md5sum $F
echo '--- 内容回读:'
cat $F
echo ''
echo '--- 与恢复模板比对（应无差异）:'
diff $F /tmp/homeEncoder_restored_ref.json && echo 'IDENTICAL' || echo 'DIFF FOUND'
