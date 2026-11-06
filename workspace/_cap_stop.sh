#!/bin/sh
echo "=== 抓包状态 ==="
ls -la /tmp/cap_ecat.pcap /tmp/cap_net.pcap 2>/dev/null
ps | grep tcpdump | grep -v grep
echo "=== 停止 ==="
for p in $(ps | grep tcpdump | grep -v grep | awk '{print $1}'); do kill $p 2>/dev/null; done
sleep 1
ls -la /tmp/cap_ecat.pcap /tmp/cap_net.pcap 2>/dev/null
cd /tmp && tar czf /tmp/cap.tgz cap_ecat.pcap cap_net.pcap 2>/dev/null
ls -la /tmp/cap.tgz
