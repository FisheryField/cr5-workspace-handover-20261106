#!/bin/sh
# 确认 homeEncoder 的加载/写入路径与时机
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== 0. 时间 ==='
date

echo ''
echo '=== 1. 日志里 homeEncoder / innerEncoder 相关行 ==='
grep -an 'homeEncoder\|innerEncoder\|EncoderHome\|home encoder' $LOG | head -20

echo ''
echo '=== 2. 09:32:39（报警前 3 秒）日志上下文（对应 log 时间 09:32:3x） ==='
awk '/2026-10-10 09:32:3[5-9]/ && NF>0 {print NR": "substr($0,1,140)}' $LOG | head -20

echo ''
echo '=== 3. 10:02-10:03（最后一次零写入+软重启）上下文 ==='
awk '/2026-10-10 10:0[12]/ && /home\|Home\|zero\|Zero\|Save\|encoder\|Encoder/ {print NR": "substr($0,1,140)}' $LOG | head -15

echo ''
echo '=== 4. 今天上午 codesys app 安装动作（谁在 09:36/09:57 装的） ==='
grep -an 'Application.app\|installApp\|UpdateApp\|download.*app\|app.*download' $LOG | head -10

echo ''
echo '=== 5. SavePos / 零点保存动作 ==='
grep -an 'SavePos\|savePos\|SetHomePos\|save.*home\|home.*save' $LOG | head -12
