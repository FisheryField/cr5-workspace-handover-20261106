#!/bin/sh
echo "=== homeEncoder.json（一行判据）==="
cat /dobot/userdata/project/settings/function/homeEncoder.json
echo
echo "=== 控制器显示的伺服版本 ==="
grep -a -A14 settVersion /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -18
echo "=== TxPDO 里那个厂商对象的 SDO 是否可读（活体验证用）==="
ls -la /dobot/userdata/project/settings/function/ 2>/dev/null | head -20
