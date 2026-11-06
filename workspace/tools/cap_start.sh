#!/bin/sh
for p in $(ps | grep tcpdump | grep -v grep | awk '{print $1}'); do kill -9 $p 2>/dev/null; done
sleep 1
rm -f /tmp/cap_ecat.pcap /tmp/cap_net.pcap
# EtherCAT：只抓非周期帧（邮箱/SDO），体积极小
/mToolServer/tcpdump -i eth0 -s 0 -w /tmp/cap_ecat.pcap 'ether proto 0x88a4 and less 1100' >/tmp/cap_ecat.err 2>&1 &
echo $! > /tmp/cap_ecat.pid
# 机器人网：抓维护工具 ↔ 控制器（排除我的 SSH）
/mToolServer/tcpdump -i eth2 -s 0 -w /tmp/cap_net.pcap 'not port 22' >/tmp/cap_net.err 2>&1 &
echo $! > /tmp/cap_net.pid
sleep 3
echo "pids: ecat=$(cat /tmp/cap_ecat.pid) net=$(cat /tmp/cap_net.pid)"
ps | grep tcpdump | grep -v grep
ls -la /tmp/cap_ecat.pcap /tmp/cap_net.pcap 2>/dev/null
echo "--- err ---"; head -3 /tmp/cap_ecat.err /tmp/cap_net.err 2>/dev/null
