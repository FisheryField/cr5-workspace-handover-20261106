echo '=== servoParams.json 是否存在 ==='
ls -la /dobot/userdata/project/settings/function/servoParams.json 2>/dev/null || echo '不存在'
echo
echo '=== settings/function 下最近新增/修改的文件 ==='
ls -lat /dobot/userdata/project/settings/function/ 2>/dev/null | head -15
echo
echo '=== settings 下所有 json（按时间）==='
ls -lat /dobot/userdata/project/settings/ 2>/dev/null | head -12
echo
echo '=== servoParams.json 内容（前 120 行）==='
head -120 /dobot/userdata/project/settings/function/servoParams.json 2>/dev/null
echo
echo '=== 文件大小 ==='
wc -c /dobot/userdata/project/settings/function/servoParams.json 2>/dev/null
echo
echo '=== 日志里的 sdo 读写记录（本次开机后）==='
for L in /dobot/userdata/CR5_sys_files/project/logs/all/log /dobot/userdata/project/logs/all/log; do
  [ -f "$L" ] && grep -a -oE "sdo (read|write)[^\"]{0,80}" "$L" 2>/dev/null | tail -20
done
echo
echo '=== 日志里 sdo index map / servo params 相关 ==='
for L in /dobot/userdata/CR5_sys_files/project/logs/all/log; do
  [ -f "$L" ] && grep -a -oE "(init sdo index map|SDOWRCount = [0-9]+|IsWriteFromFile=[a-z]+|parseAndReqSetServoParams[^\"]{0,40})" "$L" 2>/dev/null | tail -15
done
