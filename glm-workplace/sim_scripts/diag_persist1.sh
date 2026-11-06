#!/bin/sh
# 只读取证：跨冷启动复现问题——历史 0x86 模式 + 健康基线 + 总线重初始化记录
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== A. 控制器时间与开机时长 ==='
date
cat /proc/uptime

echo ''
echo '=== B. 使能历史（最近 8 次，行号+时间） ==='
grep -an 'robot enabled ,begin' $LOG | tail -8

echo ''
echo '=== C. 历史 0x86 + 其后 3 帧 gActual（判定每次都在哪个参考系） ==='
awk '/index=0x86,isOn=1/{print "0x86 @line "NR; c=3} /robot disabled,this enable last/{print "  [ts] "$0} /PoseTrace: gActualPosition/{if(c>0){sub(/^.*gActualPosition: */,"");print "  gA: "$0; c--}}' $LOG | tail -60

echo ''
echo '=== D. 09:32 报警之后有没有 EtherCAT 总线重初始化 ==='
grep -an 'IoDrvEtherCAT' $LOG | awk -F: '$1>383100' | head -12

echo ''
echo '=== E. 报警前那次长使能（健康基线）的 gActual ==='
en2=$(grep -an 'robot enabled ,begin' $LOG | awk -F: '$1<383100{last=$1} END{print last}')
echo "healthy enable at line $en2"
awk -v s=$en2 -v e=383135 'NR>=s&&NR<=e' $LOG | grep -a 'gActualPosition' | sed 's/^.*gActualPosition: */  gA: /' | head -3
echo '  --- 报警瞬间前后（09:32:42）:'
awk -v e=383135 'NR>=e-120&&NR<=e+30' $LOG | grep -a 'gActualPosition\|logServoError\|index=0x8' | sed 's/^.*PoseTrace: gActualPosition: */  gA: /' | head -14

echo ''
echo '=== F. 0x82/0x83 IO 板报警位全部历史（置位/复位与时间） ==='
grep -an 'index=0x82\|index=0x83' $LOG | tail -14

echo ''
echo '=== G. 上电计数与 gcontrol 重启标记 ==='
grep -an 'm_powerCnt' $LOG | tail -3
grep -an 'create shm' $LOG | tail -4

echo ''
echo '=== H. TryLockForRead 异常的上下文 ==='
ln=$(grep -an 'TryLockForRead#41 lock_num' $LOG | tail -1 | cut -d: -f1)
[ -n "$ln" ] || ln=1
awk -v s=$((ln-3)) -v e=$((ln+3)) 'NR>=s&&NR<=e' $LOG | cut -c1-200
