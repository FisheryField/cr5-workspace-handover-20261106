#!/bin/sh
L=/dobot/userdata/CR5_sys_files/project/logs/codesys/log
echo "=== SDO 片段（前 120 条）==="
grep -ao "SDO[^A-Za-z]\{0,1\}[A-Za-z0-9#:. ]\{0,90\}" $L 2>/dev/null | head -120
echo
echo "=== 含 16# 的片段（前 120）==="
grep -ao "16#[0-9A-Fa-f]\{1,8\}[^,]\{0,60\}" $L 2>/dev/null | head -120
