#!/bin/sh
# 使能前闸门（只读）：判定当前反馈处于定基系还是原始系
# 判据：J5 定基系恒在 -90 附近（P1 姿态）；原始系在 +16 附近。分界 -40。
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== 最近一次驱动 PowerOn ==='
grep -an 'PowerOn m_powerCnt' $LOG | tail -2

po_line=$(grep -an 'PowerOn m_powerCnt' $LOG | tail -1 | cut -d: -f1)
echo "  (log line $po_line)"
echo ''

echo '=== PowerOn 之后的 gActualPosition（最后 3 条） ==='
grep -an 'PoseTrace: gActualPosition' $LOG | awk -F: -v p="$po_line" '$1 > p' | tail -3

last=$(grep -an 'PoseTrace: gActualPosition' $LOG | awk -F: -v p="$po_line" '$1 > p' | tail -1)
if [ -z "$last" ]; then
  echo ''
  echo '!! PowerOn 后还没有 PoseTrace —— 驱动可能还没上电，先在面板执行上电再跑本脚本'
  exit 0
fi
echo ''
echo '=== 判定 ==='
echo "$last" | sed 's/.*gActualPosition://' | tr -d ' ' | awk -F, '{
  j5=$5+0;
  printf "  J1=%.2f J2=%.2f J3=%.2f J4=%.2f J5=%.2f J6=%.2f\n", $1,$2,$3,$4,$5,$6;
  if (j5 > -40) print "  >> 原始编码器系（RAW）—— 禁止使能！会使能即 0x86 下坠";
  else           print "  >> 定基系（CALIB）—— 反馈正常，可以清报警后使能";
}'
echo ''
echo '=== 当前报警残留 ==='
grep -a 'monitorErrorStatus' $LOG | tail -1
