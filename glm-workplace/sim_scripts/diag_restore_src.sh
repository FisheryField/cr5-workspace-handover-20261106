#!/bin/sh
# 找驱动参数/零点的恢复源 + 确认 0x83 板现状
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log

echo '=== 0. 时间 ==='
date

echo ''
echo '=== 1. SavePos 相关文件 ==='
ls -la /dobot/userdata/savepos_backup/ 2>/dev/null
find /dobot/userdata -name 'SavePos*' 2>/dev/null | head -10

echo ''
echo '=== 2. settings 目录树（两层） ==='
find /dobot/userdata/CR5_sys_files/project/settings -maxdepth 2 -type f 2>/dev/null | head -40

echo ''
echo '=== 3. servo/zero/param 类文件全盘 ==='
find /dobot/userdata -iname '*servo*' -type f 2>/dev/null | grep -v logs | head -15
find /dobot/userdata -iname '*param*' -type f 2>/dev/null | grep -v logs | head -15

echo ''
echo '=== 4. 当前 boot 的 unio 固件版本检查（0x82 板） ==='
grep -an 'firmware\|Firmware\|2\.3\.[0-9]\|mailbox\|Mailbox' $LOG | sed -n '1,12p' | cut -c1-160

echo ''
echo '=== 5. 9/27 标零后驱动侧有没有收到 SDO 写（历史 log 里 0x2x 索引写） ==='
grep -ac 'Index: 16#2' $LOG
grep -a 'Index: 16#2' $LOG | tail -5 | cut -c1-160

echo ''
echo '=== 6. SlaveLog 当前从站清单（0x83 板回来没有） ==='
tail -45 /dobot/userdata/SlaveLog 2>/dev/null | grep -a 'ProductID\|SoftVersion\|Slave_Nums\|Terminal\|CoRobot\|vid' | head -20
